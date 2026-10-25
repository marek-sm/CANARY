"""Guards in the bounded agent loop (audit A-11)."""

import pytest

from agent.loop import MAX_STEPS, run_loop
from runner.mock_provider import MockProvider


def _loop(script, **kwargs):
    return run_loop(
        MockProvider(script),
        [{"role": "user", "content": "task"}],
        tool_schemas=[],
        decoding={},
        model_request={"model": "mock"},
        on_attempt=lambda *args: None,
        **kwargs,
    )


def test_the_default_step_limit_is_eight():
    # SPEC.md Section 4: "the default maximum is eight".
    assert MAX_STEPS == 8
    cut_off = {"stop_reason": "max_tokens", "content": [{"type": "text", "text": "more"}]}
    outcome = _loop([cut_off] * (MAX_STEPS + 1))
    assert (outcome.termination_reason, outcome.steps_used) == ("max_steps", 8)


@pytest.mark.parametrize("max_steps", [0, -1])
def test_a_step_limit_below_one_is_refused(max_steps):
    with pytest.raises(ValueError):
        _loop([], max_steps=max_steps)


def test_a_call_to_a_tool_the_runner_cant_dispatch_is_malformed_output():
    calls = []
    raw = {"stop_reason": "tool_use", "content": [
        {"type": "tool_use", "id": "c1", "name": "send_email", "input": {"to": "a@fixture.test", "subject": "s", "body": "b"}}]}
    outcome = _loop([raw], dispatch=lambda request: calls.append(request) or {"ok": True},
                    on_tool=lambda *args: None, supported_tools=("read_file",))
    assert outcome.termination_reason == "malformed_model_output"
    assert calls == []
