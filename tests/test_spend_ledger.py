"""The spend and pilot ledger, and the lead's cap, offline: every paid provider here is a
local fake or a stubbed HTTP transport, and every path is under pytest's temporary directory."""

import importlib.util
import json
import os
import pwd
from pathlib import Path

import pytest

from runner import execute, grid_dev, paid_run, spend_ledger
from runner.mock_provider import MockProvider
from runner.mock_slice import read_jsonl

ROOT = Path(__file__).resolve().parents[1]
REAL_ACCOUNT_HOME = spend_ledger._account_home  # taken before any fixture stands in for it


def _attempt(input_tokens=1000, output_tokens=100, outcome="model_response"):
    return {"event_type": "provider_attempt",
            "payload": {"outcome": outcome, "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens}}}


def _lines():
    return [json.loads(line) for line in spend_ledger.ledger_path().read_text(encoding="utf-8").splitlines()]


class Paid:
    adapter_version = "fake-paid-adapter-v0"


# --- where it lives -----------------------------------------------------------------------------


def test_the_ledger_and_cap_live_outside_every_checkout_and_no_variable_moves_them(monkeypatch):
    monkeypatch.setenv("HOME", "/elsewhere")
    assert spend_ledger._password_home() == Path(pwd.getpwuid(os.getuid()).pw_dir)
    source = Path(spend_ledger.__file__).read_text(encoding="utf-8")
    assert "getenv" not in source and "expanduser" not in source and ".home()" not in source
    assert spend_ledger.ledger_path(Path("/given/ledger.jsonl")) == Path("/given/ledger.jsonl")
    assert spend_ledger.cap_path(Path("/given/cap.json")) == Path("/given/cap.json")
    monkeypatch.setattr(spend_ledger, "_account_home", spend_ledger._password_home)  # only computes the path
    assert spend_ledger.ledger_path() == Path(pwd.getpwuid(os.getuid()).pw_dir) / ".canary" / "spend_ledger.jsonl"
    assert spend_ledger.cap_path() == Path(pwd.getpwuid(os.getuid()).pw_dir) / ".canary" / "spend_cap.json"


def test_tests_can_t_reach_the_real_canary_home():
    """However a test gets here, the real function refuses: only the stand-in in conftest answers."""
    with pytest.raises(spend_ledger.LedgerError, match="pytest"):
        REAL_ACCOUNT_HOME()


def test_init_seeds_the_october_10_check():
    spend_ledger.init()
    assert spend_ledger.totals(spend_ledger.read()) == (0.00014, 1)
    assert _lines()[0]["phase"] == "seed"


def test_init_never_overwrites_a_ledger():
    spend_ledger.init()
    start = spend_ledger.start(Paid(), "trial")
    with pytest.raises(spend_ledger.LedgerError, match="already"):
        spend_ledger.init()
    assert any(line.get("invocation_id") == start for line in _lines())


def test_a_given_path_overrides_the_default(tmp_path):
    ledger, cap = tmp_path / "a" / "ledger.jsonl", tmp_path / "b" / "cap.json"
    spend_ledger.init(ledger)
    spend_ledger.set_cap(3.0, cap)
    assert not spend_ledger.ledger_path().exists()
    assert spend_ledger.read_cap(cap) == 3.0
    assert spend_ledger.refusal(ledger=ledger, cap=cap) is None


def test_the_commands(capsys, tmp_path):
    assert spend_ledger.main(["init"]) == 0
    assert spend_ledger.main(["init"]) == 1
    assert spend_ledger.main(["set-cap", "9.5"]) == 0
    assert spend_ledger.main(["show"]) == 0
    printed = capsys.readouterr()
    assert "9.5" in printed.out and "0.00014" in printed.out and "already" in printed.err
    assert spend_ledger.main(["set-cap", "-1"]) == 1


# --- it refuses rather than reading as zero -----------------------------------------------------


def test_a_missing_ledger_isn_t_zero():
    spend_ledger.set_cap(10.0)
    reason = spend_ledger.refusal()
    assert "no spend ledger" in reason and "runner.spend_ledger init" in reason
    with pytest.raises(spend_ledger.LedgerError):
        spend_ledger.start(Paid(), "trial")


@pytest.mark.parametrize("text", [
    "not json\n",
    "",  # no seed
    '{"schema_version": "1.0.0", "phase": "seed"}\n',  # fails its schema
])
def test_a_corrupt_ledger_refuses(text):
    spend_ledger.set_cap(10.0)
    path = spend_ledger.ledger_path()
    path.write_text(text, encoding="utf-8")
    assert "corrupt" in spend_ledger.refusal()


def test_a_torn_last_line_refuses_and_says_how_to_repair_it():
    spend_ledger.init()
    spend_ledger.set_cap(10.0)
    path = spend_ledger.ledger_path()
    path.write_text(path.read_text(encoding="utf-8").rstrip("\n"), encoding="utf-8")
    reason = spend_ledger.refusal()
    assert "corrupt" in reason and "delete that partial line" in reason and "console" in reason


def test_a_second_seed_refuses():
    spend_ledger.init()
    spend_ledger.set_cap(10.0)
    path = spend_ledger.ledger_path()
    path.write_text(path.read_text(encoding="utf-8") * 2, encoding="utf-8")
    assert "corrupt" in spend_ledger.refusal()


def test_a_finish_with_no_start_or_two_finishes_refuses():
    spend_ledger.init()
    spend_ledger.set_cap(10.0)
    entry = spend_ledger.start(Paid(), "trial")
    spend_ledger.finish(entry, [_attempt()])
    spend_ledger.finish(entry, [_attempt()])
    assert "corrupt" in spend_ledger.refusal()


@pytest.mark.parametrize("text", ["not json", "{}", '{"cap_usd": -1}', '{"cap_usd": 0}', '{"cap_usd": true}',
                                  '{"cap_usd": "10"}', '{"cap_usd": NaN}', '{"cap_usd": Infinity}'])
def test_a_corrupt_cap_refuses(text):
    spend_ledger.init()
    path = spend_ledger.cap_path()
    path.write_text(text, encoding="utf-8")
    assert "cap" in spend_ledger.refusal()
    assert spend_ledger.cap_or_none() is None


def test_a_missing_cap_refuses_and_says_how_it_should_be_set():
    spend_ledger.init()
    reason = spend_ledger.refusal()
    assert "set-cap" in reason and "below the workspace limit" in reason


# --- what it counts -----------------------------------------------------------------------------


def test_usage_is_priced_at_the_frozen_rates():
    spend_ledger.init()
    entry = spend_ledger.start(Paid(), "trial")
    spend_ledger.finish(entry, [_attempt(1000, 100), _attempt(2000, 200)])
    expected = 3000 * 0.10 / 1_000_000 + 300 * 0.50 / 1_000_000
    assert spend_ledger.totals(spend_ledger.read())[0] == pytest.approx(0.00014 + expected)
    finished = _lines()[-1]
    assert (finished["attempts"], finished["input_tokens"], finished["output_tokens"]) == (2, 3000, 300)
    assert finished["unknown_usage_attempts"] == 0


def test_a_prompt_over_the_price_step_takes_the_higher_rates():
    assert spend_ledger.attempt_usd({"input_tokens": 100_001, "output_tokens": 10}) == pytest.approx(
        100_001 * 0.50 / 1_000_000 + 10 * 2.50 / 1_000_000)


@pytest.mark.parametrize("usage", [None, {}, {"input_tokens": None, "output_tokens": 5}, {"input_tokens": 5, "output_tokens": None},
                                   {"input_tokens": True, "output_tokens": 5}])
def test_an_attempt_with_no_recorded_usage_is_never_priced_at_zero(usage):
    assert spend_ledger.attempt_usd(usage) == spend_ledger.REQUEST_BOUND_USD


def test_a_trial_killed_after_its_start_stays_at_its_bound():
    spend_ledger.init()
    spend_ledger.start(Paid(), "trial")
    spend, trials = spend_ledger.totals(spend_ledger.read())
    assert spend == pytest.approx(0.00014 + spend_ledger.TRIAL_BOUND_USD)
    assert trials == 2


def test_a_resumed_trial_is_no_new_trial_but_its_attempts_cost():
    spend_ledger.init()
    spend_ledger.finish(spend_ledger.start(Paid(), "trial"), [_attempt()])
    spend_ledger.finish(spend_ledger.start(Paid(), "trial", new_trial=False), [_attempt()])
    spend, trials = spend_ledger.totals(spend_ledger.read())
    assert trials == 2
    assert spend == pytest.approx(0.00014 + 2 * spend_ledger.attempt_usd(_attempt()["payload"]["usage"]))


def test_only_development_trials_count_against_the_ceiling():
    spend_ledger.init()
    spend_ledger.start(Paid(), "trial", split="evaluation")
    assert spend_ledger.totals(spend_ledger.read())[1] == 1


def test_the_ceiling_is_section_9_s_120():
    spend_ledger.init()
    spend_ledger.set_cap(1000.0)
    for index in range(119):
        spend_ledger.finish(spend_ledger.start(Paid(), f"trial-{index}"), [_attempt()])
    assert spend_ledger.refusal(new_trials=0) is None
    reason = spend_ledger.refusal(new_trials=1)
    assert "120" in reason and "Section 9" in reason


@pytest.mark.parametrize("over", [False, True])
def test_the_check_is_spend_plus_one_trial_s_bound_against_the_cap(over):
    spend_ledger.init()
    spend_ledger.set_cap(0.00014 + spend_ledger.TRIAL_BOUND_USD + (-1e-9 if over else 1e-9))
    reason = spend_ledger.refusal()
    assert (reason is not None and "cap" in reason) if over else reason is None


def test_the_bound_and_rates_are_the_frozen_ones():
    """TODO(#70): the module's constants move to analysis/price_bound.py; until then they must match it."""
    if importlib.util.find_spec("analysis.price_bound") is None:
        from analysis import gate2_budget

        assert spend_ledger.INPUT_USD_PER_TOKEN == gate2_budget.DEFAULT_INPUT_USD_PER_TOKEN
        assert spend_ledger.OUTPUT_USD_PER_TOKEN == gate2_budget.DEFAULT_OUTPUT_USD_PER_TOKEN
        assert spend_ledger.TRIAL_BOUND_USD == pytest.approx(0.0585216)
    else:
        from analysis import price_bound

        assert spend_ledger.TRIAL_BOUND_USD == price_bound.PRICE_BOUND_USD


def test_the_ledger_stays_outside_the_hashed_paths():
    assert not spend_ledger.ledger_path().is_relative_to(ROOT)
    assert not any(path.startswith((".canary", "protocol/spend")) for path in paid_run.tracked_files())


# --- on the runner paths, with fake providers ------------------------------------------------------


class FakePaid:
    """A paid provider to the gate, the delivery mock underneath; it never leaves this process."""

    adapter_version = "fake-paid-adapter-v0"

    def __init__(self, inner, calls, usage, raises=None):
        self.inner, self.calls, self.usage, self.raises = inner, calls, usage, raises

    def complete(self, messages, tool_schemas, decoding, model_request):
        self.calls.append(model_request["model"])
        if self.raises and len(self.calls) == self.raises[0]:
            raise self.raises[1]
        return {**self.inner.complete(messages, tool_schemas, decoding, model_request),
                "model_resolved": model_request["model"], "usage": self.usage}


class Killed(BaseException):
    """A forced stop; not an Exception, so the runner doesn't catch it."""


def _paid_grid(gate, out, count=None, *, usage=None, raises=None, resume=False):
    corpus = gate.root / "corpus" / "development"
    calls = []
    usage = usage or {"input_tokens": 1000, "output_tokens": 100}
    schedule = grid_dev.validate_grid_spec(gate.spec)[:count]

    def factory(trial, canaries):
        return FakePaid(execute.delivery_provider_factory(corpus)(trial, canaries), calls, usage, raises)

    return calls, lambda: execute.run_schedule(out, schedule, corpus_root=corpus, spec=gate.spec, delivery=True,
                                               provider_factory=factory, resume=resume)


def test_each_paid_trial_appends_its_priced_usage(gate, tmp_path):
    gate.open()
    calls, run = _paid_grid(gate, tmp_path / "grid", 2)
    run()
    lines = _lines()
    assert [line["phase"] for line in lines] == ["seed", "started", "finished", "started", "finished"]
    assert lines[1]["cap_usd"] == 10.0 and lines[1]["new_trial"] is True and lines[1]["provider_adapter"] == "fake-paid-adapter-v0"
    assert sum(line.get("attempts", 0) for line in lines) == len(calls)
    expected = 0.00014 + len(calls) * spend_ledger.attempt_usd({"input_tokens": 1000, "output_tokens": 100})
    assert spend_ledger.totals(spend_ledger.read()) == (pytest.approx(expected), 3)


def test_the_check_runs_before_each_trial_s_first_call(gate, tmp_path):
    gate.open()
    # Room for this seed and one trial's bound, then a first trial that spends it all.
    spend_ledger.set_cap(0.00014 + spend_ledger.TRIAL_BOUND_USD)
    usage = {"input_tokens": 1_000_000, "output_tokens": 0}
    calls, run = _paid_grid(gate, tmp_path / "grid", 3, usage=usage)
    with pytest.raises(paid_run.PaidRunRefused, match="cap"):
        run()
    first_trial_calls = len(calls)
    assert first_trial_calls >= 1
    assert sum(1 for line in _lines() if line["phase"] == "started") == 1  # no second trial started


def test_a_killed_paid_trial_is_charged_and_its_resume_counts_once(gate, tmp_path):
    gate.open()
    calls, run = _paid_grid(gate, tmp_path / "grid", 1, raises=(2, Killed()))
    with pytest.raises(Killed):
        run()
    spend, trials = spend_ledger.totals(spend_ledger.read())
    assert spend == pytest.approx(0.00014 + spend_ledger.TRIAL_BOUND_USD) and trials == 2
    _, resume = _paid_grid(gate, tmp_path / "grid", 1, resume=True)
    resume()
    started = [line for line in _lines() if line["phase"] == "started"]
    assert [line["new_trial"] for line in started] == [True, False]
    assert spend_ledger.totals(spend_ledger.read())[1] == 2


def test_a_mock_grid_writes_no_ledger_line(gate):
    gate.rerun()
    assert [line["phase"] for line in _lines()] == ["seed"]


def test_a_mock_provider_needs_neither_ledger_nor_cap():
    assert paid_run.is_paid(MockProvider()) is False
    paid_run.require_paid_run(MockProvider(), record_path=Path("/nonexistent/record.json"))


def test_a_live_grid_counts_only_what_it_hasn_t_started(gate, tmp_path, monkeypatch):
    schedule = grid_dev.validate_grid_spec(gate.spec)
    assert grid_dev.new_trials(None, gate.spec) == 90
    assert grid_dev.new_trials(tmp_path / "absent", gate.spec) == 90
    for trial in schedule[:40]:
        (tmp_path / execute.trial_slug(trial)).mkdir()
        (tmp_path / execute.trial_slug(trial) / "events.jsonl").write_text("", encoding="utf-8")
    assert grid_dev.new_trials(tmp_path, gate.spec) == 50


# --- a resume adds attempts, never a trial ------------------------------------------------------


def _at_ceiling(trials=120):
    """Fill the ledger with finished development trials, up to ``trials`` with its seed."""
    while spend_ledger.totals(spend_ledger.read())[1] < trials:
        spend_ledger.finish(spend_ledger.start(Paid(), "filler"), [])


def test_a_resume_at_the_ceiling_is_no_new_trial(gate, tmp_path):
    gate.open()
    _, run = _paid_grid(gate, tmp_path / "grid", 1, raises=(2, Killed()))
    with pytest.raises(Killed):
        run()
    _at_ceiling()
    assert "120" in spend_ledger.refusal(new_trials=1)
    calls, resume = _paid_grid(gate, tmp_path / "grid", 1, resume=True)
    resume()  # a new trial would be the 121st
    assert calls
    assert spend_ledger.totals(spend_ledger.read())[1] == 120


def test_a_new_trial_at_the_ceiling_is_refused_before_any_call(gate, tmp_path):
    gate.open()
    _at_ceiling()
    calls, run = _paid_grid(gate, tmp_path / "grid", 1)
    with pytest.raises(paid_run.PaidRunRefused, match="120"):
        run()
    assert calls == []


def test_a_resume_doesn_t_price_old_attempts_again(gate, tmp_path):
    gate.open()
    first, run = _paid_grid(gate, tmp_path / "grid", 1, raises=(2, Killed()))
    with pytest.raises(Killed):
        run()
    assert len(first) == 2  # one attempt durable, and the second stopped before it was recorded
    calls, resume = _paid_grid(gate, tmp_path / "grid", 1, resume=True)
    resume()
    finished = _lines()[-1]
    assert finished["phase"] == "finished" and finished["attempts"] == len(calls)
    assert finished["cost_usd"] == pytest.approx(len(calls) * spend_ledger.attempt_usd({"input_tokens": 1000, "output_tokens": 100}))


# --- the sweep, and the trials that aren't development trials ------------------------------------


def _other_split_grid(gate, out, count=3, *, resume=False, **labels):
    corpus = gate.root / "corpus" / "development"
    spec = {**gate.spec, "experiment_id": "sweep", "protocol_sentinel": "v1.0.0"}
    calls = []
    usage = {"input_tokens": 1000, "output_tokens": 100}

    def factory(trial, canaries):
        return FakePaid(execute.delivery_provider_factory(corpus)(trial, canaries), calls, usage)

    schedule = grid_dev.validate_grid_spec(spec)[:count]
    return schedule, calls, lambda: execute.run_schedule(out, schedule, corpus_root=corpus, spec=spec, delivery=True,
                                                         provider_factory=factory, resume=resume, **labels)


EVALUATION = {"split": "evaluation", "protocol_version": "1.0.0", "analysis_role": "primary_indirect"}


def test_the_sweep_runs_past_the_development_ceiling(gate, tmp_path):
    """The review's probe: at 116 a fake sweep ran 4 trials, refused, and wrote them as development."""
    gate.open()
    _at_ceiling(116)
    schedule, calls, run = _other_split_grid(gate, tmp_path / "sweep", 6, **EVALUATION)
    run()
    assert calls
    for trial in schedule:
        [record] = read_jsonl(tmp_path / "sweep" / execute.trial_slug(trial) / "results.jsonl", "result")
        assert (record["split"], record["protocol_version"], record["analysis_role"]) == ("evaluation", "1.0.0", "primary_indirect")
    assert spend_ledger.totals(spend_ledger.read())[1] == 116
    started = [line for line in _lines() if line["phase"] == "started" and line["split"] == "evaluation"]
    assert len(started) == 6


def test_the_sweep_runs_with_the_ceiling_already_full(gate, tmp_path):
    gate.open()
    _at_ceiling()
    _, calls, run = _other_split_grid(gate, tmp_path / "sweep", 2, **EVALUATION)
    run()
    assert calls


def test_the_sweep_still_counts_in_dollars(gate, tmp_path):
    gate.open()
    spend, _ = spend_ledger.totals(spend_ledger.read())
    spend_ledger.set_cap(spend + spend_ledger.TRIAL_BOUND_USD + 0.5 * spend_ledger.TRIAL_BOUND_USD)
    corpus = gate.root / "corpus" / "development"
    spec = {**gate.spec, "experiment_id": "sweep", "protocol_sentinel": "v1.0.0"}
    usage = {"input_tokens": 1_000_000, "output_tokens": 0}  # one trial spends past what's left
    calls = []

    def factory(trial, canaries):
        return FakePaid(execute.delivery_provider_factory(corpus)(trial, canaries), calls, usage)

    with pytest.raises(paid_run.PaidRunRefused, match="cap"):
        execute.run_schedule(tmp_path / "sweep", grid_dev.validate_grid_spec(spec)[:3], corpus_root=corpus, spec=spec,
                             delivery=True, provider_factory=factory, **EVALUATION)
    assert sum(1 for line in _lines() if line["phase"] == "started" and line["split"] == "evaluation") == 1


def test_an_evaluation_split_without_its_protocol_refuses_before_any_write(gate, tmp_path):
    for labels, words in (({"split": "evaluation"}, "protocol_version"), ({"split": "stage"}, "split")):
        _, calls, run = _other_split_grid(gate, tmp_path / "sweep", 1, **labels)
        with pytest.raises(ValueError, match=words):
            run()
        assert calls == [] and not (tmp_path / "sweep").exists()


def test_an_evaluation_split_needs_trial_ids_from_its_protocol(gate, tmp_path):
    corpus = gate.root / "corpus" / "development"
    spec = {**gate.spec, "experiment_id": "sweep"}  # its ids still say "unfrozen"
    with pytest.raises(ValueError, match="unfrozen"):
        execute.run_schedule(tmp_path / "sweep", grid_dev.validate_grid_spec(spec)[:1], corpus_root=corpus, spec=spec,
                             delivery=True, **EVALUATION)


@pytest.mark.parametrize("role", ["demo_rehearsal", "demo_stage"])
def test_rehearsal_and_stage_trials_stay_outside_the_ceiling(gate, tmp_path, role):
    """The locked result schema's ``split`` is development or evaluation, so these keep the
    development split, and ``analysis_role``, a free string there, says what they are."""
    gate.open()
    _at_ceiling()
    schedule, calls, run = _other_split_grid(gate, tmp_path / "demo", 2, split="development", analysis_role=role)
    run()
    assert calls
    [record] = read_jsonl(tmp_path / "demo" / execute.trial_slug(schedule[0]) / "results.jsonl", "result")
    assert (record["split"], record["analysis_role"]) == ("development", role)
    spend, trials = spend_ledger.totals(spend_ledger.read())
    assert trials == 120 and spend > 0.00014


def test_a_run_can_t_be_resumed_under_another_split(gate, tmp_path):
    gate.open()
    _, _, run = _other_split_grid(gate, tmp_path / "sweep", 1, **EVALUATION)
    run()
    _, calls, resume = _other_split_grid(gate, tmp_path / "sweep", 1, resume=True)
    with pytest.raises(ValueError, match="mode"):
        resume()
    assert calls == []


def test_a_development_run_records_what_it_always_did(gate, tmp_path):
    gate.open()
    calls, run = _paid_grid(gate, tmp_path / "grid", 1)
    run()
    assert json.loads((tmp_path / "grid" / execute.MODE_FILE).read_text()) == {"delivery": True}
    [record] = read_jsonl(next((tmp_path / "grid").glob("*/results.jsonl")), "result")
    assert (record["split"], record["protocol_version"], record["analysis_role"]) == ("development", None, None)


# --- the other paid paths -------------------------------------------------------------------------


def test_the_mock_slice_paid_path_is_ledgered(tmp_path, monkeypatch):
    """Reachable only by passing a provider to ``run_mock_trial``, and gated there, so it counts.
    Its events don't keep usage, so each attempt counts as the largest request."""
    from runner import mock_slice

    class PaidScript(MockProvider):
        adapter_version = "fake-paid-adapter-v0"

    monkeypatch.setattr(paid_run, "is_paid", lambda provider: True)
    monkeypatch.setattr(paid_run, "paid_run_refusal", lambda **kwargs: None)
    spend_ledger.init()
    mock_slice.run_mock_trial(tmp_path / "trial", PaidScript())
    started, finished = _lines()[1:]
    assert started["logical_trial_id"] == mock_slice.LOGICAL_TRIAL_ID
    assert finished["attempts"] == 2 and finished["unknown_usage_attempts"] == 2
    assert finished["cost_usd"] == pytest.approx(2 * spend_ledger.REQUEST_BOUND_USD)


@pytest.mark.filterwarnings("ignore:.*found in sys.modules:RuntimeWarning")
def test_this_module_run_a_second_time_can_t_touch_the_real_home(monkeypatch, capsys):
    """The review's probe: ``runpy`` gets a fresh copy of the module, without the stand-in."""
    import runpy

    monkeypatch.setattr("sys.argv", ["spend_ledger", "init"])
    with pytest.raises(SystemExit) as stopped:
        runpy.run_module("runner.spend_ledger", run_name="__main__", alter_sys=False)
    assert stopped.value.code == 1
    assert "under pytest" in capsys.readouterr().err


def test_a_child_process_of_a_test_can_t_touch_the_real_home(monkeypatch):
    import subprocess
    import sys

    monkeypatch.setenv("PYTEST_CURRENT_TEST", "a child of a test")
    done = subprocess.run([sys.executable, "-m", "runner.spend_ledger", "init"], cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 1 and "under pytest" in done.stderr
