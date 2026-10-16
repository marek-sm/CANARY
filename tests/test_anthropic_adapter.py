"""Offline tests for the Anthropic Messages adapter (decision 0010).

Every test uses a real SDK client over httpx2.MockTransport: no network, no
real key, no paid call. The sentinel key must never reach a record.
"""
import json
import os

import anthropic
import httpx2
import pytest

from agent import anthropic_adapter as adapter_mod
from agent.anthropic_adapter import AnthropicMessagesAdapter
from agent.loop import CONTINUATION_PROMPT, MAX_STEPS, run_loop
from runner import live_smoke
from runner import mock_slice as base
from runner import ticket_slice
from tasks import ticket

SENTINEL = "sk-ant-test-sentinel-credential"
MODEL = "claude-haiku-5-5"
DECODING = {"endpoint": "messages", "thinking": "disabled", "effort": "medium", "max_tokens": 4096}
TOOL = ticket.TOOL_SCHEMA


def message(content, stop_reason="end_turn", **extra):
    body = {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": "claude-haiku-5-5-resolved",
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "stop_details": None,
        "usage": {"input_tokens": 11, "output_tokens": 7},
    }
    body.update(extra)
    return body


def text_body(text="done", stop_reason="end_turn", **extra):
    return message([{"type": "text", "text": text}], stop_reason, **extra)


def tool_block(path="inbox/ticket-100.txt", call_id="toolu_1"):
    return {"type": "tool_use", "id": call_id, "name": "read_file", "input": {"path": path}}


def tool_body(call_id="toolu_1"):
    return message([tool_block(call_id=call_id)], "tool_use")


def refusal_body(content=(), category="cyber"):
    return message(list(content), "refusal",
                   stop_details={"type": "refusal", "category": category, "explanation": None})


class Fake:
    """Scripted transport: each entry is a response body, raw body bytes, an int
    status, a (status, error type, error code) triple, or an exception."""

    def __init__(self, *script):
        self.script = list(script)
        self.requests = []
        self.headers = []

    def __call__(self, request):
        self.requests.append(json.loads(request.content))
        self.headers.append(dict(request.headers))
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        if isinstance(item, bytes):
            return httpx2.Response(200, content=item, headers={"request-id": "req_123", "content-type": "application/json"})
        if isinstance(item, tuple):
            status, kind, code = item
            error = {"type": kind, "message": "fake"}
            if code is not None:
                error["details"] = {"error_code": code}
            return httpx2.Response(status, json={"type": "error", "error": error, "request_id": "req_err"},
                                   headers={"request-id": "req_err"})
        if isinstance(item, int):
            return httpx2.Response(item, json={"type": "error", "error": {"type": "fake", "message": "fake"}},
                                   headers={"request-id": "req_err"})
        return httpx2.Response(200, json=item, headers={"request-id": "req_123"})

    def adapter(self):
        client = anthropic.Anthropic(api_key=SENTINEL, base_url="https://fake.invalid", max_retries=0,
                                     http_client=httpx2.Client(transport=httpx2.MockTransport(self)))
        return AnthropicMessagesAdapter(client)


def call(fake, messages=None, tools=(TOOL,), decoding=DECODING):
    messages = messages or [{"role": "system", "content": "sys"}, {"role": "user", "content": "task"}]
    return fake.adapter().complete(messages, list(tools), decoding, {"model": MODEL})


def run_ticket(tmp_path, fake):
    out = ticket_slice.run(tmp_path / "run", fake.adapter(), model=MODEL, decoding=DECODING,
                           experiment_id="live-dev-test", analysis_role="excluded_development")
    [result] = base.read_jsonl(out / base.RESULTS_FILE, "result")
    return base.read_jsonl(out / base.EVENTS_FILE, "event"), result


def of_type(events, kind):
    return [e for e in events if e["event_type"] == kind]


def loop(fake, script_tools=(), **kwargs):
    attempts = []
    outcome = run_loop(fake.adapter(), [{"role": "user", "content": "t"}], tool_schemas=list(script_tools),
                       decoding=DECODING, model_request={"model": MODEL},
                       on_attempt=lambda *a: attempts.append(a), **kwargs)
    return outcome, attempts


# Request -----------------------------------------------------------------

def test_request_translates_history_and_tools_and_omits_sampling():
    fake = Fake(text_body())
    history = [
        {"role": "system", "content": "sys"},
        {"role": "system", "content": "marking"},
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": [{"type": "text", "text": "reading"},
                                          {"type": "tool_use", "id": "toolu_1", "name": "read_file", "input": {"path": "a.txt"}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": {"ok": True, "text": "x"}}]},
        {"role": "assistant", "content": "partial"},
        {"role": "user", "content": CONTINUATION_PROMPT},
    ]
    call(fake, history)
    body = fake.requests[0]
    assert body["model"] == MODEL and body["max_tokens"] == 4096
    assert body["thinking"] == {"type": "disabled"} and body["output_config"] == {"effort": "medium"}
    assert not {"temperature", "top_p", "top_k", "tool_choice"} & set(body)
    assert body["system"] == [{"type": "text", "text": "sys"}, {"type": "text", "text": "marking"}]
    assert body["tools"] == [{"name": "read_file", "description": TOOL["description"], "input_schema": TOOL["input_schema"]}]
    assert body["messages"] == [
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": [{"type": "text", "text": "reading"},
                                          {"type": "tool_use", "id": "toolu_1", "name": "read_file", "input": {"path": "a.txt"}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": '{"ok":true,"text":"x"}'}]},
        {"role": "assistant", "content": "partial"},
        {"role": "user", "content": CONTINUATION_PROMPT},
    ]


def test_key_is_sent_as_x_api_key_only():
    fake = Fake(text_body())
    call(fake)
    headers = fake.headers[0]
    assert headers["x-api-key"] == SENTINEL and "authorization" not in headers


def test_no_tools_sends_no_tools_field():
    fake = Fake(text_body())
    call(fake, tools=())
    assert "tools" not in fake.requests[0]


@pytest.mark.parametrize("decoding", [
    {"thinking": "disabled", "effort": "medium", "max_tokens": 64},
    {"endpoint": "chat_completions", "thinking": "disabled", "effort": "medium", "max_tokens": 64},
    {"endpoint": "messages", "effort": "medium", "max_tokens": 64},
    {"endpoint": "messages", "thinking": "adaptive", "effort": "medium", "max_tokens": 64},
    {"endpoint": "messages", "thinking": "disabled", "max_tokens": 64},
    {"endpoint": "messages", "thinking": "disabled", "effort": "xhigh", "max_tokens": 64},
    {"endpoint": "messages", "thinking": "disabled", "effort": "max", "max_tokens": 64},
    {"endpoint": "messages", "thinking": "disabled", "effort": "medium"},
    {**DECODING, "max_tokens": 0},
    {**DECODING, "max_tokens": True},
    {**DECODING, "max_tokens": "4096"},
    {**DECODING, "temperature": 1},
    {**DECODING, "top_p": 0.99},
    {**DECODING, "top_k": 5},
])
def test_invalid_decoding_is_rejected_before_any_request(decoding):
    fake = Fake(text_body())
    with pytest.raises(ValueError):
        call(fake, decoding=decoding)
    assert fake.requests == []


@pytest.mark.parametrize("messages", [
    [{"role": "user", "content": "t"}, {"role": "assistant", "content": "cut off"}],
    [{"role": "user", "content": "t"}, {"role": "system", "content": "late"}],
    [{"role": "user", "content": "t"}, {"role": "assistant", "content": [
        {"type": "tool_use", "id": "toolu_1", "name": "read_file", "input": '{"path": '}]},
     {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": "x"}]}],
])
def test_unsupported_history_raises_before_any_request(messages):
    # A trailing assistant turn is a prefill, which Claude Haiku 5.5 rejects; the
    # loop never sends one (decision 0010), so reaching it is a harness defect.
    fake = Fake(text_body())
    with pytest.raises(ValueError):
        call(fake, messages)
    assert fake.requests == []


# Output-limit continuation (decision 0010) -------------------------------

def test_max_tokens_stop_continues_with_a_user_turn():
    fake = Fake(text_body("partial", stop_reason="max_tokens"), text_body("answer"))
    outcome, attempts = loop(fake)
    assert outcome.termination_reason == "final_answer" and outcome.final_text == "answer"
    assert len(fake.requests) == 2 and len(attempts) == 2
    assert fake.requests[1]["messages"] == [
        {"role": "user", "content": "t"},
        {"role": "assistant", "content": "partial"},
        {"role": "user", "content": CONTINUATION_PROMPT},
    ]


def test_empty_max_tokens_text_sends_no_empty_assistant_turn():
    fake = Fake(message([], "max_tokens"), text_body("answer"))
    outcome, _ = loop(fake)
    assert outcome.termination_reason == "final_answer"
    assert fake.requests[1]["messages"] == [{"role": "user", "content": "t"}, {"role": "user", "content": CONTINUATION_PROMPT}]


def test_repeated_max_tokens_stops_end_at_the_step_limit():
    fake = Fake(*[text_body("more", stop_reason="max_tokens")] * MAX_STEPS)
    outcome, _ = loop(fake)
    assert outcome.termination_reason == "max_steps" and len(fake.requests) == MAX_STEPS


# Response normalization and evidence -------------------------------------

def test_text_response_and_evidence():
    fake = Fake(text_body("answer"))
    response = call(fake)
    assert response["outcome"] == "model_response"
    assert response["raw_response"] == {"stop_reason": "end_turn", "content": [{"type": "text", "text": "answer"}]}
    assert response["provider_request_id"] == "req_123"
    assert response["model_requested"] == MODEL and response["model_resolved"] == "claude-haiku-5-5-resolved"
    assert response["provider_fingerprint"] is None  # Anthropic sends none
    assert response["usage"] == {"input_tokens": 11, "output_tokens": 7}
    assert response["provider_response"]["content"][0]["text"] == "answer"
    assert response["error"] is None
    assert response["requested_at"] <= response["completed_at"] and response["latency_ms"] >= 0


def test_missing_usage_stays_null():
    body = text_body()
    del body["usage"]
    assert call(Fake(body))["usage"] == {"input_tokens": None, "output_tokens": None}


def test_tool_call_is_normalized_for_the_loop():
    response = call(Fake(tool_body()))
    assert response["raw_response"] == {"stop_reason": "tool_use", "content": [tool_block()]}


@pytest.mark.parametrize("stop,expected", [("end_turn", "end_turn"), ("tool_use", "tool_use"), ("max_tokens", "max_tokens"),
                                           ("refusal", "content_filter"), ("pause_turn", "pause_turn")])
def test_stop_reason_mapping(stop, expected):
    assert call(Fake(text_body("x", stop_reason=stop)))["raw_response"]["stop_reason"] == expected


def test_thinking_block_is_a_logged_malformed_output():
    body = message([{"type": "thinking", "thinking": "", "signature": "sig"}, {"type": "text", "text": "x"}])
    outcome, attempts = loop(Fake(body))
    assert outcome.termination_reason == "malformed_model_output"
    assert attempts[0][2]["outcome"] == "model_response"


NON_FINITE = ["NaN", "-Infinity", "1e999"]


@pytest.mark.parametrize("value", NON_FINITE)
def test_non_finite_tool_input_stays_unparsed(value):
    # The canonical evidence hash (decision 0009) rejects NaN and infinity, so a
    # tool input carrying one stays a raw string and never reaches it.
    raw = ('{"id":"msg_1","type":"message","role":"assistant","model":"m","stop_reason":"tool_use",'
           '"content":[{"type":"tool_use","id":"toolu_1","name":"read_file","input":{"path":%s}}],'
           '"usage":{"input_tokens":11,"output_tokens":7}}' % value).encode()
    response = call(Fake(raw))
    assert isinstance(response["raw_response"]["content"][0]["input"], str)
    assert isinstance(response["provider_response"], str)
    base.sha256_json(response)


@pytest.mark.parametrize("value", NON_FINITE)
def test_non_finite_tool_input_is_a_logged_malformed_model_output(tmp_path, value):
    raw = ('{"id":"msg_1","type":"message","role":"assistant","model":"m","stop_reason":"tool_use",'
           '"content":[{"type":"tool_use","id":"toolu_1","name":"read_file","input":{"path":%s}}]}' % value).encode()
    events, result = run_ticket(tmp_path, Fake(raw))
    assert len(of_type(events, "provider_attempt")) == 1
    assert result["status"] == "completed" and result["termination_reason"] == "malformed_model_output"
    assert of_type(events, "tool_dispatch") == []


@pytest.mark.parametrize("content", [[{"type": "text"}], ["not-an-object"], None])
def test_unusable_content_structure(content):
    body = message([], "end_turn")
    body["content"] = content
    response = call(Fake(body))
    if content is None:
        assert response["outcome"] == "no_model_content" and response["raw_response"] is None
    else:
        assert response["outcome"] == "model_response"
        assert response["raw_response"]["content"] == [{"type": "unparseable_provider_response"}]


def strict_lines(path):
    """Every event line parses as strict JSON: no NaN or infinity reached the log."""
    def reject(name):
        raise AssertionError(f"{name} in {path.name}")
    return [json.loads(line, parse_constant=reject) for line in path.read_text().splitlines()]


@pytest.mark.parametrize("field", ['"model":NaN', '"stop_reason":NaN', '"text":NaN', '"id":NaN'])
def test_non_finite_values_outside_tool_input_never_reach_the_log(tmp_path, field):
    # Decision 0009 item 3: nothing non-finite reaches the canonical hash or the
    # event log, wherever in the provider body it appears.
    content = ('{"type":"text",%s}' % field) if field == '"text":NaN' else (
        '{"type":"tool_use",%s,"name":"read_file","input":{"path":"a"}}' % field if field == '"id":NaN'
        else '{"type":"text","text":"x"}')
    top = {'"model":NaN': '"model":NaN', '"stop_reason":NaN': '"model":"m","stop_reason":NaN'}.get(field, '"model":"m","stop_reason":"end_turn"')
    raw = ('{"id":"msg_1","type":"message","role":"assistant",%s,"content":[%s]}' % (top, content)).encode()
    events, result = run_ticket(tmp_path, Fake(raw))
    [attempt] = of_type(events, "provider_attempt")
    assert attempt["payload"]["outcome"] == "model_response" and isinstance(attempt["payload"]["provider_response"], str)
    assert result["status"] == "completed" and result["termination_reason"] == "malformed_model_output"
    strict_lines(tmp_path / "run" / base.EVENTS_FILE)
    strict_lines(tmp_path / "run" / base.RESULTS_FILE)


def test_non_string_model_is_recorded_as_null(tmp_path):
    body = text_body('{"ticket_id":"T-100","status":"open"}')
    body["model"] = 5
    events, result = run_ticket(tmp_path, Fake(tool_body(), body))
    assert [a["payload"]["model_resolved"] for a in of_type(events, "provider_attempt")] == ["claude-haiku-5-5-resolved", None]
    assert result["status"] == "completed"


@pytest.mark.parametrize("raw", [
    b'{"type":"error","error":{"type":NaN,"message":"fake","details":{"error_code":NaN}}}',
    b'{"type":"error","error":{"type":"invalid_request_error","message":"fake","details":{"error_code":{"nested":1}}}}',
    b'{"type":"error","error":{"type":["x"],"message":"fake","details":{"error_code":["x"]}}}',
])
def test_malformed_error_bodies_are_logged_with_null_type_and_code(tmp_path, raw, policy_code):
    class Malformed(Fake):
        def __call__(self, request):
            self.requests.append(json.loads(request.content))
            return httpx2.Response(400, content=raw, headers={"request-id": "req_err", "content-type": "application/json"})
    fake = Malformed()
    events, result = run_ticket(tmp_path, fake)
    attempts = of_type(events, "provider_attempt")
    assert len(attempts) == 3 and result["termination_reason"] == "infrastructure_failure"
    assert attempts[0]["payload"]["error"]["provider_code"] is None
    assert attempts[0]["payload"]["error"]["provider_type"] in (None, "invalid_request_error")
    strict_lines(tmp_path / "run" / base.EVENTS_FILE)


def test_deeply_nested_body_is_no_content():
    deep = b'{"content":' + b"[" * 100_000 + b"]" * 100_000 + b"}"
    response = call(Fake(deep))
    assert response["outcome"] == "no_model_content" and response["error"]["type"] == "invalid_body"


def test_whitespace_only_text_is_never_sent():
    # The Messages API rejects whitespace-only text, so it is dropped rather than
    # turning a cut-off reply into three rejected requests.
    fake = Fake(text_body())
    call(fake, [{"role": "user", "content": "t"}, {"role": "assistant", "content": "\n\n"},
                {"role": "user", "content": CONTINUATION_PROMPT},
                {"role": "assistant", "content": [{"type": "text", "text": "  "}, tool_block()]},
                {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": "x"}]}])
    assert fake.requests[0]["messages"] == [
        {"role": "user", "content": "t"},
        {"role": "user", "content": CONTINUATION_PROMPT},
        {"role": "assistant", "content": [tool_block()]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": "x"}]},
    ]


def test_unparseable_body_keeps_its_text():
    class Garbage(Fake):
        def __call__(self, request):
            self.requests.append(request)
            return httpx2.Response(200, text="<html>oops</html>", headers={"request-id": "req_g"})
    response = Garbage().adapter().complete([{"role": "user", "content": "t"}], [], DECODING, {"model": MODEL})
    assert response["outcome"] == "no_model_content" and response["provider_response"] == "<html>oops</html>"


# Errors and retries ---------------------------------------------------------

@pytest.mark.parametrize("failure", [500, 529, 429, "timeout", "connect"])
def test_transport_failures_are_no_content_after_one_request(failure):
    if failure == "timeout":
        failure = httpx2.TimeoutException("slow")
    elif failure == "connect":
        failure = httpx2.ConnectError("down")
    fake = Fake(failure)
    response = call(fake)
    assert len(fake.requests) == 1  # SDK max_retries=0: the loop owns retries
    assert response["outcome"] == "no_model_content" and response["raw_response"] is None
    assert response["provider_response"] is None and response["error"]["type"]
    assert SENTINEL not in json.dumps(response)


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_client_errors_are_logged_attempts_without_the_key(status):
    fake = Fake((status, "invalid_request_error", "some_code"))
    response = call(fake)
    assert response["outcome"] == "no_model_content" and response["error"]["status"] == status
    assert response["error"]["provider_type"] == "invalid_request_error" and response["error"]["provider_code"] == "some_code"
    assert "fake" not in json.dumps(response["error"])  # the message is never kept
    assert response["provider_request_id"] == "req_err" and SENTINEL not in json.dumps(response)
    assert len(fake.requests) == 1


def test_error_without_details_has_a_null_code():
    response = call(Fake((400, "invalid_request_error", None)))
    assert response["error"]["provider_code"] is None


def test_spend_limit_rejection_is_an_infrastructure_failure(tmp_path):
    limit = (429, "rate_limit_error", "enforced_spend_limit_reached")
    events, result = run_ticket(tmp_path, Fake(limit, limit, limit))
    assert {a["payload"]["outcome"] for a in of_type(events, "provider_attempt")} == {"no_model_content"}
    assert result["status"] == "infrastructure_failure" and result["termination_reason"] == "infrastructure_failure"


def test_loop_retries_twice_then_infrastructure_failure():
    fake = Fake(500, 500, 500)
    outcome, attempts = loop(fake)
    assert outcome.termination_reason == "infrastructure_failure" and len(attempts) == 3 and len(fake.requests) == 3


# Content-filter refusals (decisions 0008 and 0010) --------------------------

POLICY_CODE = "fake_content_policy_code"


@pytest.fixture
def policy_code(monkeypatch):
    # Anthropic documents no content-policy HTTP code, so the shipped set is
    # empty; tests list a fake one to exercise the rule.
    monkeypatch.setattr(adapter_mod, "CONTENT_POLICY_CODES", frozenset({POLICY_CODE}), raising=False)


def test_empty_refusal_is_one_completed_content_filter_refusal(tmp_path):
    fake = Fake(refusal_body())
    events, result = run_ticket(tmp_path, fake)
    assert len(fake.requests) == 1  # never retried
    assert result["status"] == "completed" and result["termination_reason"] == "provider_content_filter"
    assert [e["payload"]["text"] for e in of_type(events, "final_output")] == [""]
    assert result["final_output"] == "" and result["utility"]["pass"] is False
    [attempt] = of_type(events, "provider_attempt")
    assert attempt["payload"]["provider_response"]["stop_details"]["category"] == "cyber"


def test_refusal_keeps_partial_text(tmp_path):
    # SPEC.md Section 9 keeps any text the response returned, whatever the
    # provider advises about partial output.
    _, result = run_ticket(tmp_path, Fake(refusal_body([{"type": "text", "text": "partial answer"}], category=None)))
    assert result["termination_reason"] == "provider_content_filter" and result["final_output"] == "partial answer"


def test_tool_call_under_refusal_is_requested_but_not_dispatched(tmp_path):
    events, result = run_ticket(tmp_path, Fake(refusal_body([tool_block()])))
    assert [e["payload"]["requested_args"] for e in of_type(events, "tool_requested")] == [{"path": "inbox/ticket-100.txt"}]
    assert of_type(events, "tool_dispatch") == [] and of_type(events, "tool_result") == []
    assert result["termination_reason"] == "provider_content_filter" and result["final_output"] == ""
    [tool_event] = result["tool_events"]
    assert tool_event["dispatched"] is False and tool_event["blocked"] is False
    assert tool_event["effect_observed"] is False and tool_event["execution_succeeded"] is None


def test_truncated_but_valid_tool_call_under_refusal_is_still_requested(tmp_path):
    # A mid-generation decline can cut a tool input short of what the model
    # meant; a syntactically valid call is still a request (SPEC.md Section 9).
    events, _ = run_ticket(tmp_path, Fake(refusal_body([{"type": "text", "text": "Reading"}, tool_block(path="inbox/")])))
    assert [e["payload"]["requested_args"] for e in of_type(events, "tool_requested")] == [{"path": "inbox/"}]
    assert of_type(events, "tool_dispatch") == []


def test_refusal_leaves_earlier_step_evidence_unchanged(tmp_path):
    _, refused = run_ticket(tmp_path / "a", Fake(tool_body(), refusal_body()))
    _, answered = run_ticket(tmp_path / "b", Fake(tool_body(), text_body("x")))
    strip = lambda event: {k: v for k, v in event.items() if k != "evidence_refs"}
    assert [strip(e) for e in refused["tool_events"]] == [strip(e) for e in answered["tool_events"]]
    assert refused["tool_events"][0]["authorized"] is None  # unknown stays unknown


def test_listed_content_policy_rejection_is_one_completed_refusal(tmp_path, policy_code):
    rejection = (400, "invalid_request_error", POLICY_CODE)
    fake = Fake(rejection, rejection, rejection)
    events, result = run_ticket(tmp_path, fake)
    assert len(fake.requests) == 1
    assert [a["payload"]["outcome"] for a in of_type(events, "provider_attempt")] == ["provider_content_filter"]
    assert result["status"] == "completed" and result["termination_reason"] == "provider_content_filter"
    assert result["final_output"] == ""


def test_unlisted_400_is_still_an_infrastructure_failure(tmp_path, policy_code):
    rejection = (400, "invalid_request_error", "other_code")
    fake = Fake(rejection, rejection, rejection)
    _, result = run_ticket(tmp_path, fake)
    assert len(fake.requests) == 3
    assert result["status"] == "infrastructure_failure" and result["termination_reason"] == "infrastructure_failure"


# End to end through the ticket runner --------------------------------------

def test_ticket_run_with_adapter_is_schema_valid_and_key_free(tmp_path):
    fake = Fake(tool_body(), text_body('{"ticket_id":"T-100","status":"open"}'))
    events, result = run_ticket(tmp_path, fake)
    assert result["utility"]["pass"] is True and result["run_metadata"]["model_requested"] == MODEL
    assert result["run_metadata"]["temperature"] is None and result["run_metadata"]["top_p"] is None
    assert all(e["payload"]["usage"] == {"input_tokens": 11, "output_tokens": 7} for e in of_type(events, "provider_attempt"))
    assert {e["component_versions"]["provider_adapter"] for e in events} == {adapter_mod.ADAPTER_VERSION}
    assert fake.requests[1]["messages"][-1]["content"][0]["type"] == "tool_result"
    for path in (tmp_path / "run").rglob("*"):
        if path.is_file():
            assert SENTINEL not in path.read_text(errors="replace")


# Client and live command guards ----------------------------------------------

def _no_client(*args, **kwargs):
    raise AssertionError("client built")


def clear_provider_env(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    for name in [n for n in os.environ if n.startswith(("ANTHROPIC_", "OPENAI_"))]:
        monkeypatch.delenv(name)


def test_build_client_disables_retries_pins_the_url_and_ignores_proxy_env(monkeypatch):
    clear_provider_env(monkeypatch)
    seen = {}
    monkeypatch.setattr(adapter_mod.anthropic, "Anthropic", lambda **kwargs: seen.update(kwargs) or "client")
    assert adapter_mod.build_client(SENTINEL) == "client"
    assert seen["api_key"] == SENTINEL and seen["max_retries"] == 0 and seen["base_url"] == "https://api.anthropic.com"
    assert seen["http_client"]._trust_env is False


@pytest.mark.parametrize("name", ["ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "ANTHROPIC_CUSTOM_HEADERS"])
def test_build_client_refuses_ambient_anthropic_variables(monkeypatch, name):
    monkeypatch.setenv(name, "x")
    monkeypatch.setattr(adapter_mod.anthropic, "Anthropic", _no_client)
    with pytest.raises(ValueError):
        adapter_mod.build_client(SENTINEL)


def test_build_client_refuses_an_empty_key(monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setattr(adapter_mod.anthropic, "Anthropic", _no_client)
    with pytest.raises(ValueError):
        adapter_mod.build_client("")


def test_adapter_forces_sdk_retries_off():
    client = anthropic.Anthropic(api_key=SENTINEL, base_url="https://fake.invalid", max_retries=5,
                                 http_client=httpx2.Client(transport=httpx2.MockTransport(Fake(500))))
    assert AnthropicMessagesAdapter(client)._client.max_retries == 0


def env_file(tmp_path, line=f"ANTHROPIC_API_KEY={SENTINEL}\n"):
    path = tmp_path / ".env"
    path.write_text(line)
    return path


def test_live_smoke_defaults_to_the_anthropic_candidate():
    assert live_smoke.DEFAULT_PROVIDER == "anthropic"
    assert live_smoke.PROVIDERS["anthropic"]["model"] == MODEL
    assert live_smoke.PROVIDERS["anthropic"]["decoding"] == DECODING
    adapter_mod.check_decoding(live_smoke.PROVIDERS["anthropic"]["decoding"])


def test_live_smoke_refuses_in_ci_before_reading_the_key(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("CI", "")
    monkeypatch.setattr(adapter_mod, "build_client", _no_client)
    monkeypatch.setattr(live_smoke, "load_api_key", lambda *a: pytest.fail("key read in CI"))
    assert live_smoke.main(["--env-file", str(env_file(tmp_path)), "--out", str(tmp_path / "o")]) != 0
    assert not (tmp_path / "o").exists()


@pytest.mark.parametrize("name", ["ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", "OPENAI_BASE_URL"])
def test_live_smoke_refuses_ambient_provider_variables(tmp_path, monkeypatch, name):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv(name, "https://elsewhere.invalid")
    monkeypatch.setattr(adapter_mod, "build_client", _no_client)
    monkeypatch.setattr(live_smoke, "load_api_key", lambda *a: pytest.fail("key read"))
    assert live_smoke.main(["--env-file", str(env_file(tmp_path)), "--out", str(tmp_path / "o")]) != 0


@pytest.mark.parametrize("content", [None, "ANTHROPIC_API_KEY=\n", f"OPENAI_API_KEY={SENTINEL}\n"])
def test_live_smoke_refuses_missing_empty_or_wrong_key(tmp_path, monkeypatch, content):
    clear_provider_env(monkeypatch)
    path = tmp_path / ".env"
    if content is not None:
        path.write_text(content)
    monkeypatch.setattr(adapter_mod, "build_client", _no_client)
    assert live_smoke.main(["--env-file", str(path), "--out", str(tmp_path / "o")]) != 0


def test_live_smoke_runs_the_anthropic_path_and_prints_unknown_usage(tmp_path, monkeypatch, capsys):
    body = text_body('{"ticket_id":"T-100","status":"open"}')
    del body["usage"]
    fake = Fake(tool_body(), body)
    clear_provider_env(monkeypatch)
    monkeypatch.setattr(adapter_mod, "build_client", lambda key: fake.adapter()._client)
    assert live_smoke.main(["--env-file", str(env_file(tmp_path)), "--out", str(tmp_path / "o")]) == 0
    printed = capsys.readouterr().out
    assert "input tokens:     unknown" in printed and "Claude Console" in printed and SENTINEL not in printed
    assert fake.requests[0]["model"] == MODEL and fake.requests[0]["thinking"] == {"type": "disabled"}


def test_live_smoke_never_reads_unknown_usage_as_below_the_price_step(tmp_path, monkeypatch, capsys):
    body = text_body('{"ticket_id":"T-100","status":"open"}')
    del body["usage"]
    fake = Fake(tool_body(), body)
    clear_provider_env(monkeypatch)
    monkeypatch.setattr(adapter_mod, "build_client", lambda key: fake.adapter()._client)
    assert live_smoke.main(["--env-file", str(env_file(tmp_path)), "--out", str(tmp_path / "o")]) == 0
    assert "token count is unknown" in capsys.readouterr().out


def test_live_smoke_warns_above_the_long_prompt_price_step(tmp_path, monkeypatch, capsys):
    fake = Fake(tool_body(), text_body('{"ticket_id":"T-100","status":"open"}', usage={"input_tokens": 100_001, "output_tokens": 7}))
    clear_provider_env(monkeypatch)
    monkeypatch.setattr(adapter_mod, "build_client", lambda key: fake.adapter()._client)
    assert live_smoke.main(["--env-file", str(env_file(tmp_path)), "--out", str(tmp_path / "o")]) == 0
    assert "100,000" in capsys.readouterr().out
