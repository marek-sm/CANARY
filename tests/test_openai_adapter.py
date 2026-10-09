"""Offline tests for the OpenAI Chat Completions adapter (decision 0005).

Every test uses a real SDK client over httpx2.MockTransport: no network, no
real key, no paid call. The sentinel key must never reach a record.
"""
import json
from pathlib import Path

import httpx2
import openai
import pytest

from agent import openai_adapter as adapter_mod
from agent.loop import run_loop
from agent.openai_adapter import OpenAIChatAdapter
from runner import live_smoke
from runner import mock_slice as base
from runner import ticket_slice
from tasks import ticket

SENTINEL = "sk-test-sentinel-credential"
MODEL = "gpt-6-luna"
DECODING = {"endpoint": "chat_completions", "reasoning_effort": "none"}
TOOL = ticket.TOOL_SCHEMA


def completion(message, finish_reason="stop", **extra):
    body = {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 1790000000,
        "model": "gpt-6-luna-resolved",
        "choices": [{"index": 0, "message": {"role": "assistant", **message}, "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
    }
    body.update(extra)
    return body


def text_body(text="done", finish_reason="stop", **extra):
    return completion({"content": text}, finish_reason, **extra)


def tool_body(arguments='{"path": "inbox/ticket-100.txt"}', call_id="call_1"):
    call = {"id": call_id, "type": "function", "function": {"name": "read_file", "arguments": arguments}}
    return completion({"content": None, "tool_calls": [call]}, "tool_calls")


class Fake:
    """Scripted transport: each entry is a response body, an int status, a
    (status, provider error code) pair, or an exception."""

    def __init__(self, *script):
        self.script = list(script)
        self.requests = []

    def __call__(self, request):
        self.requests.append(json.loads(request.content))
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        if isinstance(item, tuple):
            status, code = item
            return httpx2.Response(status, json={"error": {"message": "fake", "type": "fake", "code": code}},
                                   headers={"x-request-id": "req_err"})
        if isinstance(item, int):
            return httpx2.Response(item, json={"error": {"message": "fake", "type": "fake"}}, headers={"x-request-id": "req_err"})
        return httpx2.Response(200, json=item, headers={"x-request-id": "req_123"})

    def adapter(self):
        client = openai.OpenAI(api_key=SENTINEL, base_url="https://fake.invalid/v1", max_retries=0,
                               http_client=httpx2.Client(transport=httpx2.MockTransport(self)))
        return OpenAIChatAdapter(client)


def call(fake, messages=None, tools=(TOOL,), decoding=DECODING):
    messages = messages or [{"role": "system", "content": "sys"}, {"role": "user", "content": "task"}]
    return fake.adapter().complete(messages, list(tools), decoding, {"model": MODEL})


# Request -----------------------------------------------------------------

def test_request_translates_history_and_tools_and_omits_sampling():
    fake = Fake(text_body())
    history = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": [{"type": "text", "text": "reading"},
                                          {"type": "tool_use", "id": "call_1", "name": "read_file", "input": {"path": "a.txt"}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "call_1", "content": {"ok": True, "text": "x"}}]},
        {"role": "assistant", "content": "partial"},
    ]
    call(fake, history)
    body = fake.requests[0]
    assert body["model"] == MODEL
    assert body["reasoning_effort"] == "none" and body["store"] is False
    assert "temperature" not in body and "top_p" not in body
    assert body["tools"] == [{"type": "function", "function": {"name": "read_file", "description": TOOL["description"], "parameters": TOOL["input_schema"]}}]
    assert body["messages"] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": "reading", "tool_calls": [
            {"id": "call_1", "type": "function", "function": {"name": "read_file", "arguments": '{"path":"a.txt"}'}}]},
        {"role": "tool", "tool_call_id": "call_1", "content": '{"ok":true,"text":"x"}'},
        {"role": "assistant", "content": "partial"},
    ]


def test_no_tools_sends_no_tools_field():
    fake = Fake(text_body())
    call(fake, tools=())
    assert "tools" not in fake.requests[0]


@pytest.mark.parametrize("decoding", [
    {"reasoning_effort": "none"},
    {"endpoint": "chat_completions"},
    {"endpoint": "responses", "reasoning_effort": "none"},
    {"endpoint": "chat_completions", "reasoning_effort": "low"},
    {**DECODING, "temperature": 0},
    {**DECODING, "top_p": 1},
    {**DECODING, "seed": 1},
])
def test_invalid_decoding_is_rejected_before_any_request(decoding):
    fake = Fake(text_body())
    with pytest.raises(ValueError):
        call(fake, decoding=decoding)
    assert fake.requests == []


def test_reasoning_effort_may_differ_without_tools_and_max_tokens_passes_through():
    fake = Fake(text_body())
    call(fake, tools=(), decoding={**DECODING, "reasoning_effort": "low", "max_completion_tokens": 64})
    assert fake.requests[0]["reasoning_effort"] == "low" and fake.requests[0]["max_completion_tokens"] == 64


# Response normalization and evidence -------------------------------------

def test_text_response_and_evidence():
    fake = Fake(text_body("answer", system_fingerprint="fp_abc"))
    response = call(fake)
    assert response["outcome"] == "model_response"
    assert response["raw_response"] == {"stop_reason": "end_turn", "content": [{"type": "text", "text": "answer"}]}
    assert response["provider_request_id"] == "req_123"
    assert response["model_requested"] == MODEL and response["model_resolved"] == "gpt-6-luna-resolved"
    assert response["provider_fingerprint"] == "fp_abc"
    assert response["usage"] == {"input_tokens": 11, "output_tokens": 7}
    assert response["provider_response"]["choices"][0]["message"]["content"] == "answer"
    assert response["error"] is None
    assert response["requested_at"] <= response["completed_at"] and response["latency_ms"] >= 0


def test_missing_fingerprint_and_usage_stay_null():
    body = text_body()
    del body["usage"]
    response = call(Fake(body))
    assert response["provider_fingerprint"] is None
    assert response["usage"] == {"input_tokens": None, "output_tokens": None}


def test_tool_call_is_normalized_for_the_loop():
    response = call(Fake(tool_body()))
    assert response["raw_response"] == {"stop_reason": "tool_use", "content": [
        {"type": "tool_use", "id": "call_1", "name": "read_file", "input": {"path": "inbox/ticket-100.txt"}}]}


@pytest.mark.parametrize("finish,stop", [("length", "max_tokens"), ("content_filter", "content_filter"), ("surprise", "surprise")])
def test_finish_reason_mapping(finish, stop):
    body = text_body("", finish_reason=finish) if finish != "surprise" else text_body("x")
    if finish == "surprise":
        body["choices"][0]["finish_reason"] = "surprise"
    assert call(Fake(body))["raw_response"]["stop_reason"] == stop


def test_unparseable_arguments_never_dispatch():
    fake = Fake(tool_body(arguments='{"path": '))
    dispatched = []
    outcome = run_loop(fake.adapter(), [{"role": "user", "content": "t"}], tool_schemas=[TOOL], decoding=DECODING,
                       model_request={"model": MODEL}, on_attempt=lambda *a: None, dispatch=dispatched.append,
                       on_tool=lambda *a: None)
    assert outcome.termination_reason == "malformed_model_output" and dispatched == []


NON_FINITE = ['{"path": NaN}', '{"path": -Infinity}', '{"path": "inbox/ticket-100.txt", "n": 1e999}']


@pytest.mark.parametrize("arguments", NON_FINITE)
def test_non_finite_arguments_stay_unparsed(arguments):
    # NaN, infinity, and 1e999 are not JSON; parsed, they would make the
    # canonical evidence hash (decision 0009) raise.
    response = call(Fake(tool_body(arguments=arguments)))
    assert response["raw_response"]["content"][0]["input"] == arguments
    base.sha256_json(response)


@pytest.mark.parametrize("arguments", NON_FINITE)
def test_non_finite_arguments_are_a_logged_malformed_model_output(tmp_path, arguments):
    events, result = run_ticket(tmp_path, Fake(tool_body(arguments=arguments)))
    assert len(of_type(events, "provider_attempt")) == 1
    assert result["status"] == "completed" and result["termination_reason"] == "malformed_model_output"
    assert of_type(events, "tool_dispatch") == []


# Errors and retries ---------------------------------------------------------

@pytest.mark.parametrize("failure", [500, 503, 429, "timeout", "connect"])
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
    # SPEC.md Section 9: every transport attempt stays logged, so a rejected
    # request returns a record the loop logs rather than raising past on_attempt.
    fake = Fake(status)
    response = call(fake)
    assert response["outcome"] == "no_model_content" and response["error"]["status"] == status
    assert response["error"]["provider_type"] == "fake" and "fake" not in json.dumps(response["error"]["type"])
    assert response["provider_request_id"] == "req_err" and SENTINEL not in json.dumps(response)
    assert len(fake.requests) == 1


def test_rejected_request_logs_every_attempt_then_infrastructure_failure(tmp_path):
    fake = Fake(401, 401, 401)
    out = ticket_slice.run(tmp_path / "run", fake.adapter(), model=MODEL, decoding=DECODING,
                           experiment_id="live-dev-test", analysis_role="excluded_development")
    attempts = [e for e in base.read_jsonl(out / base.EVENTS_FILE, "event") if e["event_type"] == "provider_attempt"]
    [result] = base.read_jsonl(out / base.RESULTS_FILE, "result")
    assert [a["payload"]["error"]["status"] for a in attempts] == [401, 401, 401]
    assert result["termination_reason"] == "infrastructure_failure" and len(result["attempts"]) == 3


# Content-filter refusals (decision 0008) ------------------------------------

POLICY_CODE = "fake_content_policy_code"


def run_ticket(tmp_path, fake):
    out = ticket_slice.run(tmp_path / "run", fake.adapter(), model=MODEL, decoding=DECODING,
                           experiment_id="live-dev-test", analysis_role="excluded_development")
    [result] = base.read_jsonl(out / base.RESULTS_FILE, "result")
    return base.read_jsonl(out / base.EVENTS_FILE, "event"), result


def of_type(events, kind):
    return [e for e in events if e["event_type"] == kind]


@pytest.fixture
def policy_code(monkeypatch):
    # OpenAI documents no Chat Completions content-policy code, so the shipped
    # set is empty; tests list a fake one to exercise the rule.
    monkeypatch.setattr(adapter_mod, "CONTENT_POLICY_CODES", frozenset({POLICY_CODE}), raising=False)


def test_listed_content_policy_rejection_is_one_completed_refusal(tmp_path, policy_code):
    fake = Fake((400, POLICY_CODE), (400, POLICY_CODE), (400, POLICY_CODE))
    events, result = run_ticket(tmp_path, fake)
    attempts = of_type(events, "provider_attempt")
    assert len(fake.requests) == 1  # never retried
    assert [a["payload"]["outcome"] for a in attempts] == ["provider_content_filter"]
    assert attempts[0]["payload"]["error"]["status"] == 400 and attempts[0]["payload"]["error"]["provider_code"] == POLICY_CODE
    assert result["status"] == "completed" and result["termination_reason"] == "provider_content_filter"
    # The final-output surface is complete and empty, so scorers see it rather than null.
    assert [e["payload"]["text"] for e in of_type(events, "final_output")] == [""]
    assert result["final_output"] == "" and result["utility"]["pass"] is False


def test_unlisted_400_is_still_an_infrastructure_failure(tmp_path, policy_code):
    fake = Fake((400, "other_code"), (400, "other_code"), (400, "other_code"))
    events, result = run_ticket(tmp_path, fake)
    assert len(fake.requests) == 3
    assert {a["payload"]["outcome"] for a in of_type(events, "provider_attempt")} == {"no_model_content"}
    assert result["status"] == "infrastructure_failure" and result["termination_reason"] == "infrastructure_failure"


def test_content_filter_finish_is_a_refusal_that_keeps_its_text(tmp_path):
    events, result = run_ticket(tmp_path, Fake(text_body("partial answer", finish_reason="content_filter")))
    assert result["status"] == "completed" and result["termination_reason"] == "provider_content_filter"
    assert result["final_output"] == "partial answer"


def test_tool_call_under_content_filter_is_requested_but_not_dispatched(tmp_path):
    call = {"id": "call_1", "type": "function", "function": {"name": "read_file", "arguments": '{"path": "inbox/ticket-100.txt"}'}}
    events, result = run_ticket(tmp_path, Fake(completion({"content": None, "tool_calls": [call]}, "content_filter")))
    assert [e["payload"]["requested_args"] for e in of_type(events, "tool_requested")] == [{"path": "inbox/ticket-100.txt"}]
    assert of_type(events, "tool_dispatch") == [] and of_type(events, "tool_result") == []
    assert result["termination_reason"] == "provider_content_filter" and result["final_output"] == ""
    [tool_event] = result["tool_events"]
    # The durable trial end proves no dispatch and no effect; execution is not applicable.
    assert tool_event["dispatched"] is False and tool_event["blocked"] is False
    assert tool_event["effect_observed"] is False and tool_event["execution_succeeded"] is None


def test_refusal_leaves_earlier_step_evidence_unchanged(tmp_path, policy_code):
    _, refused = run_ticket(tmp_path / "a", Fake(tool_body(), (400, POLICY_CODE)))
    _, answered = run_ticket(tmp_path / "b", Fake(tool_body(), text_body("x")))
    strip = lambda event: {k: v for k, v in event.items() if k != "evidence_refs"}
    assert [strip(e) for e in refused["tool_events"]] == [strip(e) for e in answered["tool_events"]]
    assert refused["tool_events"][0]["authorized"] is None  # unknown stays unknown


def test_empty_choices_is_no_content():
    body = text_body()
    body["choices"] = []
    assert call(Fake(body))["outcome"] == "no_model_content"


def test_loop_retries_twice_then_infrastructure_failure():
    fake = Fake(500, 500, 500)
    attempts = []
    outcome = run_loop(fake.adapter(), [{"role": "user", "content": "t"}], tool_schemas=[], decoding=DECODING,
                       model_request={"model": MODEL}, on_attempt=lambda *a: attempts.append(a))
    assert outcome.termination_reason == "infrastructure_failure" and len(attempts) == 3 and len(fake.requests) == 3


def test_failure_then_success_keeps_both_attempts():
    fake = Fake(429, text_body("ok"))
    attempts = []
    outcome = run_loop(fake.adapter(), [{"role": "user", "content": "t"}], tool_schemas=[], decoding=DECODING,
                       model_request={"model": MODEL}, on_attempt=lambda *a: attempts.append(a))
    assert outcome.final_text == "ok"
    assert [a[2]["outcome"] for a in attempts] == ["no_model_content", "model_response"]


# End to end through the ticket runner --------------------------------------

def test_ticket_run_with_adapter_is_schema_valid_and_key_free(tmp_path):
    fake = Fake(tool_body(), text_body('{"ticket_id":"T-100","status":"open"}'))
    out = ticket_slice.run(tmp_path / "run", fake.adapter(), model=MODEL, decoding=DECODING,
                           experiment_id="live-dev-test", analysis_role="excluded_development")
    events = base.read_jsonl(out / base.EVENTS_FILE, "event")
    [result] = base.read_jsonl(out / base.RESULTS_FILE, "result")
    assert result["utility"]["pass"] is True and result["experiment_id"] == "live-dev-test"
    assert result["run_metadata"]["model_requested"] == MODEL
    assert result["run_metadata"]["temperature"] is None and result["run_metadata"]["top_p"] is None
    attempts = [e for e in events if e["event_type"] == "provider_attempt"]
    assert all(e["payload"]["usage"] == {"input_tokens": 11, "output_tokens": 7} for e in attempts)
    assert all(e["payload"]["provider_response"]["model"] == "gpt-6-luna-resolved" for e in attempts)
    assert all("temperature" not in body and "top_p" not in body for body in fake.requests)
    assert {e["component_versions"]["provider_adapter"] for e in events} == {adapter_mod.ADAPTER_VERSION}
    for path in out.rglob("*"):
        if path.is_file():
            assert SENTINEL not in path.read_text(errors="replace")


def test_mock_ticket_events_carry_no_provider_evidence_keys(tmp_path):
    events = base.read_jsonl(ticket_slice.run(tmp_path / "run") / base.EVENTS_FILE, "event")
    for event in events:
        if event["event_type"] == "provider_attempt":
            assert "provider_response" not in event["payload"] and "usage" not in event["payload"]


# Live command guards --------------------------------------------------------

def _no_client(*args, **kwargs):
    raise AssertionError("client built")


def test_live_smoke_refuses_in_ci_before_reading_the_key(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(f"OPENAI_API_KEY={SENTINEL}\n")
    monkeypatch.setenv("CI", "")
    monkeypatch.setattr(adapter_mod, "build_client", _no_client)
    monkeypatch.setattr(live_smoke, "load_api_key", lambda path: pytest.fail("key read in CI"))
    assert live_smoke.main(["--env-file", str(env_file), "--out", str(tmp_path / "o")]) != 0
    assert not (tmp_path / "o").exists()


def test_live_smoke_refuses_ambient_openai_variables(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(f"OPENAI_API_KEY={SENTINEL}\n")
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://elsewhere.invalid")
    monkeypatch.setattr(adapter_mod, "build_client", _no_client)
    assert live_smoke.main(["--env-file", str(env_file), "--out", str(tmp_path / "o")]) != 0


@pytest.mark.parametrize("content", [None, "OPENAI_API_KEY=\n"])
def test_live_smoke_refuses_missing_or_empty_key(tmp_path, monkeypatch, content):
    env_file = tmp_path / ".env"
    if content is not None:
        env_file.write_text(content)
    monkeypatch.delenv("CI", raising=False)
    for name in [n for n in __import__("os").environ if n.startswith("OPENAI_")]:
        monkeypatch.delenv(name)
    monkeypatch.setattr(adapter_mod, "build_client", _no_client)
    assert live_smoke.main(["--env-file", str(env_file), "--out", str(tmp_path / "o")]) != 0


def test_build_client_disables_retries_pins_the_url_and_ignores_proxy_env(monkeypatch):
    for name in [n for n in __import__("os").environ if n.startswith("OPENAI_")]:
        monkeypatch.delenv(name)
    seen = {}
    monkeypatch.setattr(adapter_mod.openai, "OpenAI", lambda **kwargs: seen.update(kwargs) or "client")
    assert adapter_mod.build_client(SENTINEL) == "client"
    assert seen["max_retries"] == 0 and seen["base_url"] == "https://api.openai.com/v1"
    assert seen["http_client"]._trust_env is False


def test_build_client_refuses_ambient_openai_variables(monkeypatch):
    monkeypatch.setenv("OPENAI_CUSTOM_HEADERS", "X-Leak: 1")
    monkeypatch.setattr(adapter_mod.openai, "OpenAI", _no_client)
    with pytest.raises(ValueError):
        adapter_mod.build_client(SENTINEL)


def test_adapter_forces_sdk_retries_off():
    client = openai.OpenAI(api_key=SENTINEL, base_url="https://fake.invalid/v1", max_retries=5,
                           http_client=httpx2.Client(transport=httpx2.MockTransport(Fake(500))))
    assert OpenAIChatAdapter(client)._client.max_retries == 0


@pytest.mark.parametrize("calls", [[{"type": "function"}], ["not-an-object"], [{"id": "c", "type": "function", "function": None}]])
def test_malformed_tool_call_structure_is_a_logged_model_response(calls):
    body = completion({"content": None, "tool_calls": calls}, "tool_calls")
    fake = Fake(body)
    attempts = []
    outcome = run_loop(fake.adapter(), [{"role": "user", "content": "t"}], tool_schemas=[TOOL], decoding=DECODING,
                       model_request={"model": MODEL}, on_attempt=lambda *a: attempts.append(a),
                       dispatch=lambda r: pytest.fail("dispatched"), on_tool=lambda *a: None)
    assert outcome.termination_reason == "malformed_model_output"
    assert attempts[0][2]["outcome"] == "model_response" and attempts[0][2]["provider_response"] == body


def test_unparseable_body_keeps_its_text():
    class Garbage(Fake):
        def __call__(self, request):
            self.requests.append(request)
            return httpx2.Response(200, text="<html>oops</html>", headers={"x-request-id": "req_g"})
    response = Garbage().adapter().complete([{"role": "user", "content": "t"}], [], DECODING, {"model": MODEL})
    assert response["outcome"] == "no_model_content" and response["provider_response"] == "<html>oops</html>"


def test_live_summary_prints_unknown_usage_not_zero(tmp_path, monkeypatch, capsys):
    body = text_body('{"ticket_id":"T-100","status":"open"}')
    del body["usage"]
    fake = Fake(tool_body(), body)
    env_file = tmp_path / ".env"
    env_file.write_text(f"OPENAI_API_KEY={SENTINEL}\n")
    monkeypatch.delenv("CI", raising=False)
    for name in [n for n in __import__("os").environ if n.startswith("OPENAI_")]:
        monkeypatch.delenv(name)
    monkeypatch.setattr(adapter_mod, "build_client", lambda key: fake.adapter()._client)
    assert live_smoke.main(["--env-file", str(env_file), "--out", str(tmp_path / "o")]) == 0
    printed = capsys.readouterr().out
    assert "input tokens:     unknown" in printed and SENTINEL not in printed


def test_no_workflow_runs_the_live_command():
    workflows = Path(__file__).resolve().parent.parent / ".github" / "workflows"
    for path in workflows.glob("*.y*ml"):
        text = path.read_text(encoding="utf-8")
        assert "live-smoke" not in text and "live_smoke" not in text, path.name
