"""Grid usage reaches the results and the Gate 2 budget equation (W7-T3).

A live grid cell's provider attempts carry token usage and latency. They must
survive into each attempt's durable event and the result's summed ``usage``,
because ``analysis.gate2_budget`` prices every trial from that block. A usage
count the provider didn't return stays unknown, and the budget equation refuses
it rather than pricing the trial at zero.
"""

import json
from pathlib import Path

import pytest

from analysis import gate2_budget
from runner import delivery, execute, grid_dev
from runner.mock_provider import MOCK_MODEL_ID
from runner.mock_slice import EVENTS_FILE, RESULTS_FILE, read_jsonl
from runner.schedule import generate_schedule

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpus" / "development"
SPEC_PATH = ROOT / "protocol" / "development_grid_spec.json"
COMMIT = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"


def _metered_factory(calls):
    """Delivery's task mock, reporting the usage and latency a real adapter returns."""

    def factory(trial, canaries):
        base = json.loads((CORPUS / f"{trial.base_case_id}.json").read_text(encoding="utf-8"))
        template, _ = delivery.task_for(base, trial.channel)
        provider = delivery.DeliveryTaskMock(template, trial.channel)
        original = provider.complete

        def complete(*args, **kwargs):
            response = dict(original(*args, **kwargs))
            n = len(calls) + 1
            response["usage"] = {"input_tokens": 1000 * n, "output_tokens": 10 * n}
            response["latency_ms"] = n
            calls.append(response)
            return response

        provider.complete = complete
        return provider

    return factory


def _run_first_cell(out, factory):
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    spec["model_id"] = MOCK_MODEL_ID
    schedule = generate_schedule(spec)[:1]
    tokens = iter(f"{i:08x}" for i in range(50))
    execute.run_schedule(
        out, schedule, corpus_root=CORPUS, spec=spec, provider_factory=factory,
        clock=lambda: "2020-01-01T00:00:00Z", code_commit_value=COMMIT,
        canary_factory=lambda: next(tokens), delivery=True,
    )
    return schedule[0]


def test_attempt_usage_reaches_events_results_and_budget(tmp_path):
    calls = []
    trial = _run_first_cell(tmp_path / "run", _metered_factory(calls))
    trial_dir = tmp_path / "run" / execute.trial_slug(trial)
    attempts = [e["payload"] for e in read_jsonl(trial_dir / EVENTS_FILE, "event") if e["event_type"] == "provider_attempt"]
    assert calls and len(attempts) == len(calls)
    assert [a.get("usage") for a in attempts] == [c["usage"] for c in calls]
    assert [a.get("latency_ms") for a in attempts] == [c["latency_ms"] for c in calls]

    result = read_jsonl(trial_dir / RESULTS_FILE, "result")[0]
    assert result["usage"]["input_tokens"] == sum(c["usage"]["input_tokens"] for c in calls)
    assert result["usage"]["output_tokens"] == sum(c["usage"]["output_tokens"] for c in calls)
    assert result["usage"]["latency_ms"] == sum(c["latency_ms"] for c in calls)
    assert gate2_budget.trial_cost_usd(result) > 0


def test_budget_refuses_unknown_usage_instead_of_pricing_it_at_zero():
    record = {"usage": {"provider_requests": 2, "input_tokens": None, "output_tokens": None, "latency_ms": None}}
    with pytest.raises(ValueError, match="usage"):
        gate2_budget.trial_cost_usd(record)


def _attempt(outcome, usage):
    return {"event_type": "provider_attempt", "attempt_id": "t:step1:a1", "payload": {"outcome": outcome, "usage": usage}}


def test_budget_prices_from_events_when_the_result_total_is_unknown():
    record = {"usage": {"provider_requests": 3, "input_tokens": None, "output_tokens": None, "latency_ms": None}}
    events = [
        _attempt("no_model_content", {"input_tokens": None, "output_tokens": None}),
        _attempt("model_response", {"input_tokens": 400, "output_tokens": 40}),
        _attempt("model_response", {"input_tokens": 600, "output_tokens": 60}),
    ]
    expected = 1000 * gate2_budget.DEFAULT_INPUT_USD_PER_TOKEN + 100 * gate2_budget.DEFAULT_OUTPUT_USD_PER_TOKEN
    assert gate2_budget.trial_cost_usd(record, events) == pytest.approx(expected)
    events.append(_attempt("model_response", {"input_tokens": None, "output_tokens": None}))
    with pytest.raises(ValueError, match="without recorded usage"):
        gate2_budget.trial_cost_usd(record, events)


def test_budget_cli_requires_the_reserve_term(tmp_path, capsys):
    with pytest.raises(SystemExit):
        gate2_budget.main([str(tmp_path), "--remaining-balance-usd", "9.9", "--conservative-c1-trial-cost-usd", "0.03"])
    assert "--reserve-usd" in capsys.readouterr().err


def test_grid_usage_summary_counts_unknown_usage_apart():
    known = {"channel": "C2", "configuration": "D0_BASELINE", "usage": {"provider_requests": 2, "input_tokens": 900, "output_tokens": 90}}
    unknown = {"channel": "C2", "configuration": "D0_BASELINE", "usage": {"provider_requests": 2, "input_tokens": None, "output_tokens": None}}
    bucket = grid_dev.usage_by_channel_configuration([(known, []), (unknown, [])])["C2/D0_BASELINE"]
    assert bucket["trials"] == 2 and bucket["usage_unknown_trials"] == 1
    assert bucket["input_tokens"] == 900 and bucket["output_tokens"] == 90
