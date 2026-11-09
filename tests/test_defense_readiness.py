"""W7-T4's predeclared binary readiness checks (SPEC.md Section 12, rule 3).

The grids here are synthetic records built from the schema fixture, so each
test fails exactly one predeclared rule and shows the script names it. They
also pin the property the project lead relies on: the decision never reads an
attack or utility outcome.
"""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from analysis import defense_readiness as dr
from analysis.defense_readiness import D1, D2, defense_readiness, main
from runner.mock_provider import MOCK_MODEL_ID

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = json.loads((ROOT / "tests" / "fixtures" / "result" / "valid_development.json").read_text(encoding="utf-8"))
RESULT_VALIDATOR = Draft202012Validator(json.loads((ROOT / "schemas" / "result.schema.json").read_text(encoding="utf-8")))
EVENT_VALIDATOR = Draft202012Validator(json.loads((ROOT / "schemas" / "event.schema.json").read_text(encoding="utf-8")))

BASES = dr.DEVELOPMENT_BASES
CHANNELS = dr.CHANNELS
MODEL = "claude-haiku-5-5"
CONFIGS = ("D0_BASELINE", D1, D2)


def tool_event(call_id="c1", *, authorized=True, dispatched=True, blocked=False, match=True, observed=True, gate=True):
    decision = {"authorized": authorized, "reason_codes": [] if authorized else ["path_not_authorized"], "evaluator_version": "t"}
    return {
        "call_id": call_id, "step": 1, "tool": "read_file", "requested_args": {"path": "a.txt"},
        "normalized_args": {"path": "a.txt"}, "normalizer_version": "n", "request_evaluable": True,
        "authorized": authorized, "gate_decision": decision if gate else None, "audit_decision": decision,
        "gate_audit_match": match, "blocked": blocked, "dispatched": dispatched, "disposition_observed": observed,
        "execution_succeeded": True if dispatched else None, "effect_observed": None, "effect_oracle_id": "o", "sink_received": None,
        "evidence_refs": [],
    }


REQUESTS: dict[str, list] = {}


def result(base, channel, condition, configuration, *, tool_events=None, input_tokens=1000, requests=None, status="completed", run_index=1):
    record = copy.deepcopy(TEMPLATE)
    trial = f"grid-dev:unfrozen:{MODEL}:{base}:{channel}:{condition}:{configuration}:r{run_index}"
    record.update(split="development", experiment_id="grid-dev", logical_trial_id=trial, base_case_id=base,
                  case_id=f"{base}:{channel}:{condition}", channel=channel, condition=condition,
                  configuration=configuration, status=status, run_index=run_index)
    record["run_metadata"].update(model_requested=MODEL, model_resolved=MODEL)
    requests = list(requests) if requests is not None else [input_tokens]
    REQUESTS[trial] = requests
    record["usage"]["input_tokens"] = None if None in requests else sum(requests)
    record["usage"]["provider_requests"] = len(requests)
    record["attempts"] = [
        {"attempt_id": f"{trial}:step{i}:a1", "model_call_id": f"{trial}:step{i}", "step": i, "attempt_index": 1,
         "provider_request_id": None, "outcome": "model_response"}
        for i in range(1, len(requests) + 1)
    ]
    if configuration == D1:
        record["tool_events"] = tool_events if tool_events is not None else [tool_event()]
    RESULT_VALIDATOR.validate(record)
    return record


def events(record, stop="end_turn", usage=True):
    trial = record["logical_trial_id"]
    common = {"schema_version": "1.0.0", "experiment_id": record["experiment_id"], "logical_trial_id": trial,
              "configuration": record["configuration"], "recorded_at": "2026-10-20T00:00:00Z",
              "raw_evidence": {"sha256": None, "artifact_ref": None},
              "component_versions": {"runner": "t", "agent_loop": "t", "provider_adapter": "t"}}
    log = [
        {**common, "event_id": f"{trial}:e1", "sequence": 1, "event_type": "trial_started", "model_call_id": None,
         "attempt_id": None, "payload": {"model_requested": MODEL, "max_steps": 6}},
    ]
    for i, tokens in enumerate(REQUESTS[trial], start=1):
        payload = {"step": i, "attempt_index": 1, "outcome": "model_response", "provider_request_id": None,
                   "model_requested": MODEL, "model_resolved": MODEL, "provider_fingerprint": None,
                   "raw_response": {"stop_reason": stop, "content": []}}
        if usage:
            payload["usage"] = {"input_tokens": tokens, "output_tokens": 10}
        log.append({**common, "event_id": f"{trial}:e{i + 1}", "sequence": i + 1, "event_type": "provider_attempt",
                    "model_call_id": f"{trial}:step{i}", "attempt_id": f"{trial}:step{i}:a1",
                    "raw_evidence": {"sha256": "0" * 64, "artifact_ref": None}, "payload": payload})
    for event in log:
        EVENT_VALIDATOR.validate(event)
    return log


def grid(**kwargs):
    trials = []
    for base in BASES:
        for channel in CHANNELS:
            for condition in ("attack", "clean"):
                for configuration in CONFIGS:
                    record = result(base, channel, condition, configuration, **kwargs.get(configuration, {}))
                    trials.append((record, events(record)))
    return trials


def run(trials, **kwargs):
    kwargs.setdefault("context_window", 200_000)
    kwargs.setdefault("output_reserve", 20_000)
    return defense_readiness(trials, run_code_checks=False, **kwargs)


def failed(report, defense):
    return {c["check"] for c in report["defenses"][defense]["checks"] if not c["passed"]}


def replace(trials, index, record):
    out = list(trials)
    out[index] = (record, out[index][1])
    return out


def find(trials, configuration, base="dev-001", channel="C2", condition="attack"):
    for i, (record, _) in enumerate(trials):
        if (record["configuration"], record["base_case_id"], record["channel"], record["condition"]) == (configuration, base, channel, condition):
            return i, record
    raise AssertionError("cell not found")


def test_a_clean_grid_makes_both_defenses_ready():
    report = run(grid())
    assert report["defenses"][D1]["decision"] == "ready"
    assert report["defenses"][D2]["decision"] == "ready"
    assert report["trials_read"] == 90


def test_d1_denied_request_that_dispatched_is_not_ready():
    bad = [tool_event(authorized=False, dispatched=True, blocked=False)]
    report = run(grid(**{D1: {"tool_events": bad}}))
    assert "D1-NO-BLOCKED-DISPATCH" in failed(report, D1)
    assert report["defenses"][D2]["decision"] == "ready"  # one defense's failure never fails the other


def test_d1_denied_request_must_be_recorded_blocked():
    only = [tool_event(authorized=False, dispatched=False, blocked=None)]
    assert "D1-NO-BLOCKED-DISPATCH" in failed(run(grid(**{D1: {"tool_events": only}})), D1)


def test_d1_correctly_blocked_requests_are_ready():
    ok = [tool_event(authorized=False, dispatched=False, blocked=True)]
    assert run(grid(**{D1: {"tool_events": ok}}))["defenses"][D1]["decision"] == "ready"


def test_d1_gate_audit_disagreement_is_not_ready():
    assert "D1-AGREE" in failed(run(grid(**{D1: {"tool_events": [tool_event(match=False)]}})), D1)


def test_d1_unknown_agreement_is_not_ready():
    assert "D1-AGREE" in failed(run(grid(**{D1: {"tool_events": [tool_event(match=None)]}})), D1)


def test_d1_gate_that_could_not_evaluate_is_not_ready():
    report = run(grid(**{D1: {"tool_events": [tool_event(gate=False, match=None)]}}))
    assert {"D1-DECIDED", "D1-EXERCISED"} <= failed(report, D1)


def test_d1_unobserved_disposition_is_not_ready():
    assert "D1-OBSERVED" in failed(run(grid(**{D1: {"tool_events": [tool_event(observed=None)]}})), D1)


def test_d1_gate_that_never_ran_is_not_ready():
    assert "D1-EXERCISED" in failed(run(grid(**{D1: {"tool_events": []}})), D1)


def test_a_missing_cell_names_the_cell():
    trials = grid()
    i, _ = find(trials, D1, "dev-003", "C4", "clean")
    del trials[i]
    report = run(trials)
    cells = next(c for c in report["defenses"][D1]["checks"] if c["check"] == "D1-CELLS")
    assert not cells["passed"] and cells["evidence"] == ["dev-003:C4:clean missing"]


def test_an_incomplete_or_rerun_cell_is_not_ready():
    trials = grid()
    i, record = find(trials, D2)
    bad = copy.deepcopy(record)
    bad.update(status="infrastructure_failure", termination_reason="infrastructure_failure")
    assert "D2-CELLS" in failed(run(replace(trials, i, bad)), D2)

    j, record = find(grid(), D2)
    rerun = result("dev-001", "C2", "attack", D2, run_index=2)
    assert "D2-CELLS" in failed(run(replace(grid(), j, rerun)), D2)


def test_d2_needs_recorded_input_tokens_and_a_supplied_window():
    trials = grid()
    i, record = find(trials, D2)
    trials[i] = (record, events(record, usage=False))  # the model_response attempt records no input_tokens
    assert "D2-USAGE" in failed(run(trials), D2)
    assert "D2-CONTEXT" in failed(run(grid(), context_window=None, output_reserve=None), D2)


def test_d2_context_fit_is_arithmetic_on_the_largest_input():
    assert run(grid(**{D2: {"input_tokens": 180_000}}))["defenses"][D2]["decision"] == "ready"
    assert "D2-CONTEXT" in failed(run(grid(**{D2: {"input_tokens": 180_001}})), D2)


def test_d2_truncated_trial_is_not_ready():
    trials = grid()
    i, record = find(trials, D2)
    trials[i] = (record, events(record, stop="max_tokens"))
    assert "D2-NO-TRUNCATION" in failed(run(trials), D2)


def test_refuses_mock_evaluation_mixed_and_duplicate_records():
    trials = grid()
    record = copy.deepcopy(trials[0][0])
    record["run_metadata"].update(model_requested=MOCK_MODEL_ID, model_resolved=MOCK_MODEL_ID)
    with pytest.raises(ValueError, match="mock"):
        run(replace(trials, 0, record))

    other = copy.deepcopy(trials[1][0])
    other["experiment_id"] = "grid-other"
    with pytest.raises(ValueError, match="exactly one"):
        run(replace(trials, 1, other))

    with pytest.raises(ValueError, match="duplicate"):
        run(trials + [trials[0]])


def test_decision_is_outcome_blind():
    """Flip every attack and utility outcome; no readiness decision may move."""
    base = run(grid())
    out = []
    for record, ev in grid():
        record = copy.deepcopy(record)
        for key in record["security"]:
            if isinstance(record["security"][key], bool):
                record["security"][key] = not record["security"][key]
        for key in record["utility"]:
            if isinstance(record["utility"][key], bool):
                record["utility"][key] = not record["utility"][key]
        out.append((record, ev))
    assert run(out)["defenses"] == base["defenses"]


def test_code_checks_fail_when_a_test_is_skipped(monkeypatch):
    class Proc:
        returncode = 0
        stdout = "1 skipped in 0.01s\n"
        stderr = ""

    monkeypatch.setattr(dr, "_run_pytest", lambda files: (Proc.returncode, Proc.stdout + Proc.stderr))
    check = dr.run_tests("D1-TESTS", ("tests/test_policy_gate.py",))
    assert not check["passed"] and "skip" in check["detail"]


def test_code_checks_pass_on_a_clean_run(monkeypatch):
    class Proc:
        returncode = 0
        stdout = "12 passed in 0.4s\n"
        stderr = ""

    monkeypatch.setattr(dr, "_run_pytest", lambda files: (Proc.returncode, Proc.stdout + Proc.stderr))
    assert dr.run_tests("D2-TESTS", ("tests/test_datamarking.py",))["passed"]


def test_cli_refuses_an_empty_run(tmp_path, capsys):
    assert main([str(tmp_path)]) == 1
    assert "no results.jsonl" in capsys.readouterr().err


# --- Review findings on PR #54 (P1 evidence, P2 per-request fit, P2 deselection, P2 budgets) ---


def d2_with_events(mutate, **kwargs):
    trials = grid(**kwargs)
    i, record = find(trials, D2)
    trials[i] = (record, mutate(events(record)))
    return trials


def test_d2_missing_provider_trace_is_not_ready():
    report = run(d2_with_events(lambda log: [e for e in log if e["event_type"] != "provider_attempt"]))
    assert report["defenses"][D2]["decision"] == "not_ready"
    assert "D2-NO-TRUNCATION" in failed(report, D2)
    check = next(c for c in report["defenses"][D2]["checks"] if c["check"] == "D2-NO-TRUNCATION")
    assert any("no provider_attempt events" in line for line in check["evidence"])


def test_d2_trace_missing_an_attempt_the_result_lists_is_not_ready():
    trials = grid(**{D2: {"requests": [1000, 1000]}})
    i, record = find(trials, D2)
    log = events(record)
    trials[i] = (record, log[:-1])  # drops the second attempt's event
    assert "D2-NO-TRUNCATION" in failed(run(trials), D2)


def test_d2_attempt_without_a_stop_reason_is_not_ready():
    def drop(log):
        for e in log:
            if e["event_type"] == "provider_attempt":
                e["payload"]["raw_response"] = {"content": []}
        return log

    assert "D2-NO-TRUNCATION" in failed(run(d2_with_events(drop)), D2)


def test_d2_context_fit_is_per_request_not_the_trial_total():
    two_fit = {D2: {"requests": [100_000, 100_000]}}
    report = run(grid(**two_fit), context_window=150_000, output_reserve=20_000)
    assert report["defenses"][D2]["decision"] == "ready"  # each request is 120,000 with its reserve; the sum would not fit
    big = {D2: {"requests": [100_000, 140_000]}}
    assert "D2-CONTEXT" in failed(run(grid(**big), context_window=150_000, output_reserve=20_000), D2)


def test_d2_unknown_request_size_is_not_skipped():
    def strip(log):
        for e in log:
            if e["event_type"] == "provider_attempt":
                e["payload"].pop("usage", None)
        return log

    report = run(d2_with_events(strip))
    assert {"D2-CONTEXT", "D2-USAGE"} <= failed(report, D2)


@pytest.mark.parametrize("window,reserve", [(500, -1000), (0, 0), (-5, 10), (True, 0), (1000, True), (1000.5, 0)])
def test_invalid_budgets_are_refused(window, reserve):
    with pytest.raises(ValueError):
        run(grid(), context_window=window, output_reserve=reserve)


def test_cli_refuses_invalid_budgets_before_reading_the_run(tmp_path, capsys):
    assert main([str(tmp_path), "--context-window", "500", "--output-reserve", "-1000"]) == 1
    assert "output reserve must not be negative" in capsys.readouterr().err
    assert main([str(tmp_path), "--context-window", "0", "--output-reserve", "0"]) == 1
    assert "context window must be positive" in capsys.readouterr().err


def test_code_checks_reject_a_deselected_partial_run(monkeypatch):
    class Proc:
        returncode = 0
        stdout = "1 passed, 218 deselected in 0.02s\n"
        stderr = ""

    monkeypatch.setattr(dr, "_run_pytest", lambda files: (Proc.returncode, Proc.stdout + Proc.stderr))
    check = dr.run_tests("D1-TESTS", ("tests/test_policy_gate.py",))
    assert not check["passed"] and "deselected" in check["detail"]


@pytest.mark.parametrize("line", ["3 passed, 1 xfailed in 0.1s", "3 passed, 1 error in 0.1s", "3 passed, 1 xpassed in 0.1s"])
def test_code_checks_reject_xfail_xpass_and_errors(monkeypatch, line):
    class Proc:
        returncode = 0
        stdout = line + "\n"
        stderr = ""

    monkeypatch.setattr(dr, "_run_pytest", lambda files: (Proc.returncode, Proc.stdout + Proc.stderr))
    assert not dr.run_tests("D1-TESTS", ("tests/x.py",))["passed"]


def test_code_checks_strip_inherited_pytest_options(monkeypatch, tmp_path):
    """PYTEST_ADDOPTS=-k must not narrow the predeclared suite; run it for real."""
    suite = tmp_path / "test_suite.py"
    suite.write_text("def test_a():\n    pass\n\n\ndef test_b():\n    pass\n", encoding="utf-8")
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k test_a")
    check = dr.run_tests("D1-TESTS", (str(suite),))
    assert check["passed"] and "2 passed" in check["detail"] and "deselected" not in check["detail"]


def test_readiness_refuses_a_run_scored_by_changed_gate2_code(tmp_path, monkeypatch, capsys):
    """Decision 0028 and docs/INTERFACES.md: like floor_count and gate2_budget, the readiness
    script calls paid_run.check_code_matches_run before it reads a run, so a threshold
    edited after the grid is refused."""
    from runner import paid_run

    called = []

    def refuse(run_dir):
        called.append(Path(run_dir))
        raise paid_run.PaidRunRefused("the Gate 2 scoring code differs from what ran the grid")

    monkeypatch.setattr(paid_run, "check_code_matches_run", refuse)
    assert main([str(tmp_path), "--context-window", "200000", "--output-reserve", "40000"]) == 1
    assert called == [tmp_path]
    assert "differs from what ran the grid" in capsys.readouterr().err


# --- Lead-side review findings, November 9 (decision 0031 item 8): real-record shapes ---


def with_failed_first_attempt(record, log):
    """Step 1's first attempt timed out and its retry answered, as both adapters record it:
    the failed attempt has null usage, so the runner's summed trial total is null."""
    record = copy.deepcopy(record)
    trial = record["logical_trial_id"]
    failed_id = f"{trial}:step1:a0"
    record["attempts"].insert(0, {"attempt_id": failed_id, "model_call_id": f"{trial}:step1", "step": 1,
                                  "attempt_index": 1, "provider_request_id": None, "outcome": "no_model_content"})
    record["usage"]["provider_requests"] += 1
    record["usage"]["input_tokens"] = None
    RESULT_VALIDATOR.validate(record)
    first = next(e for e in log if e["event_type"] == "provider_attempt")
    failed = copy.deepcopy(first)
    failed.update(event_id=f"{trial}:e-failed", attempt_id=failed_id)
    failed["payload"].update(outcome="no_model_content", raw_response=None,
                             usage={"input_tokens": None, "output_tokens": None})
    EVENT_VALIDATOR.validate(failed)
    return record, [log[0], failed, *log[1:]]


def test_d2_a_retried_attempt_without_usage_is_ready():
    trials = grid()
    i, record = find(trials, D2)
    trials[i] = with_failed_first_attempt(record, events(record))
    report = run(trials)
    assert report["defenses"][D2]["decision"] == "ready", failed(report, D2)


def test_d1_denied_request_whose_tool_ran_is_not_ready():
    ran = tool_event(authorized=False, dispatched=False, blocked=True)
    ran["execution_succeeded"] = True  # a tool_result exists for a call the gate denied
    assert "D1-NO-BLOCKED-DISPATCH" in failed(run(grid(**{D1: {"tool_events": [ran]}})), D1)
    sent = tool_event(authorized=False, dispatched=False, blocked=True)
    sent["sink_received"] = True  # the sink received what the gate denied
    assert "D1-NO-BLOCKED-DISPATCH" in failed(run(grid(**{D1: {"tool_events": [sent]}})), D1)


def filtered_tool_event(step=1):
    """runner/execute.py's shape for a tool request in a reply the provider's filter stopped."""
    event = tool_event(gate=False, match=None, observed=False, dispatched=False, blocked=False)
    event.update(step=step, sink_received=False, effect_observed=False)
    return event


def ended(record, log, termination="provider_content_filter", steps_used=1):
    record = copy.deepcopy(record)
    record["termination_reason"] = termination
    RESULT_VALIDATOR.validate(record)
    last = log[-1]
    end = {**{k: last[k] for k in ("schema_version", "experiment_id", "logical_trial_id", "configuration",
                                   "recorded_at", "component_versions")},
           "event_id": f"{record['logical_trial_id']}:end", "sequence": last["sequence"] + 1,
           "event_type": "trial_ended", "model_call_id": None, "attempt_id": None,
           "raw_evidence": {"sha256": None, "artifact_ref": None},
           "payload": {"status": "completed", "termination_reason": termination, "steps_used": steps_used}}
    EVENT_VALIDATOR.validate(end)
    return record, [*log, end]


def test_d1_content_filter_stop_with_a_tool_request_is_ready():
    """Decision 0008: a filtered reply is a completed outcome whose request was never gated."""
    trials = grid()
    i, record = find(trials, D1)
    record = copy.deepcopy(record)
    record["tool_events"] = [tool_event(), filtered_tool_event(step=1)]
    trials[i] = ended(record, events(record))
    report = run(trials)
    assert report["defenses"][D1]["decision"] == "ready", failed(report, D1)


def test_d1_filter_exemption_needs_the_trial_to_have_ended_filtered_at_that_step():
    trials = grid()
    i, record = find(trials, D1)
    record = copy.deepcopy(record)
    record["tool_events"] = [tool_event(), filtered_tool_event(step=1)]
    trials[i] = ended(record, events(record), termination="final_answer")
    assert {"D1-DECIDED", "D1-OBSERVED"} <= failed(run(trials), D1)
    trials = grid()
    i, record = find(trials, D1)
    record = copy.deepcopy(record)
    record["tool_events"] = [tool_event(), filtered_tool_event(step=1)]
    trials[i] = ended(record, events(record), steps_used=2)
    assert {"D1-DECIDED", "D1-OBSERVED"} <= failed(run(trials), D1)


def test_d2_content_policy_refusal_with_no_response_is_ready():
    trials = grid()
    i, record = find(trials, D2)
    record = copy.deepcopy(record)
    record["attempts"][0]["outcome"] = "provider_content_filter"
    log = events(record)
    for e in log:
        if e["event_type"] == "provider_attempt":
            e["payload"].update(outcome="provider_content_filter", raw_response=None,
                                usage={"input_tokens": None, "output_tokens": None})
    record["usage"]["input_tokens"] = None
    trials[i] = ended(record, log)
    report = run(trials)
    assert report["defenses"][D2]["decision"] == "ready", failed(report, D2)


def test_d2_unrecognized_stop_reason_is_not_ready():
    """An adapter passes an unknown stop reason through; it can't rule truncation out."""
    trials = grid()
    i, record = find(trials, D2)
    trials[i] = (record, events(record, stop="model_context_window_exceeded"))
    assert "D2-NO-TRUNCATION" in failed(run(trials), D2)


def test_code_checks_fail_closed_when_not_bound_to_the_grid_code(monkeypatch):
    ran = []
    monkeypatch.setattr(dr, "_run_pytest", lambda files: ran.append(files) or (0, "5 passed in 0.1s\n"))
    report = defense_readiness(grid(), context_window=200_000, output_reserve=20_000,
                               code_binding=(False, "the test files differ from the grid's commit"))
    for defense, check_id in ((D1, "D1-TESTS"), (D2, "D2-TESTS")):
        check = next(c for c in report["defenses"][defense]["checks"] if c["check"] == check_id)
        assert not check["passed"] and "grid's commit" in check["detail"]
    assert ran == []
    unbound = defense_readiness(grid(), context_window=200_000, output_reserve=20_000)
    assert unbound["defenses"][D1]["decision"] == unbound["defenses"][D2]["decision"] == "not_ready"


def _git(root, *args):
    import subprocess
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=root,
                          check=True, capture_output=True, text=True).stdout.strip()


def bound_repo(tmp_path):
    from runner import paid_run

    root = tmp_path / "repo"
    for path in dr.BOUND_FILES:
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(f"# {path}\n", encoding="utf-8")
    (root / "defenses").mkdir()
    (root / "defenses" / "gate.py").write_text("GATE = 1\n", encoding="utf-8")
    _git(root.parent, "init", "-q", str(root))
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "grid")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    line = {"code_commit": _git(root, "rev-parse", "HEAD"),
            "code_digest": paid_run.code_digest(paid_run.code_hashes(root)), "dirty_paths": []}
    (run_dir / "code_provenance.jsonl").write_text(json.dumps(line) + "\n", encoding="utf-8")
    return root, run_dir


def test_code_binding_ties_the_suites_to_the_code_that_ran_the_grid(tmp_path):
    root, run_dir = bound_repo(tmp_path)
    assert dr.code_binding(run_dir, root=root)[0]

    (root / dr.D1_TEST_FILES[0]).write_text("# edited after the grid\n", encoding="utf-8")
    assert not dr.code_binding(run_dir, root=root)[0]  # uncommitted test edit
    _git(root, "commit", "-qam", "edit a golden test")
    assert not dr.code_binding(run_dir, root=root)[0]  # committed test edit after the grid

    root, run_dir = bound_repo(tmp_path / "second")
    (root / "defenses" / "gate.py").write_text("GATE = 2\n", encoding="utf-8")
    _git(root, "commit", "-qam", "fix the gate after the grid")
    ok, detail = dr.code_binding(run_dir, root=root)
    assert not ok and "defenses" in detail

    (run_dir / "code_provenance.jsonl").unlink()
    assert not dr.code_binding(run_dir, root=root)[0]


def test_cli_passes_the_code_binding_to_the_report(tmp_path, monkeypatch):
    from runner import paid_run

    seen = {}
    monkeypatch.setattr(paid_run, "check_code_matches_run", lambda run_dir: "compared")
    monkeypatch.setattr(dr, "code_binding", lambda run_dir: (False, "not bound"))
    monkeypatch.setattr(dr, "load_run", lambda run_dir: grid())

    def fake(trials, **kwargs):
        seen.update(kwargs)
        return {"defenses": {}}

    monkeypatch.setattr(dr, "defense_readiness", fake)
    out = tmp_path / "report.json"
    assert main([str(tmp_path), "--context-window", "200000", "--output-reserve", "20000", "--out", str(out)]) == 0
    assert seen["code_binding"] == (False, "not bound")
    assert json.loads(out.read_text())["code_binding"] == {"bound": False, "detail": "not bound"}


@pytest.mark.parametrize("env", ["FORCE_COLOR", "PY_COLORS"])
def test_code_checks_count_outcomes_whatever_the_terminal_settings(monkeypatch, tmp_path, env):
    suite = tmp_path / f"test_suite_color_{env.lower()}.py"  # a module name no other in-process run has imported
    suite.write_text("def test_a():\n    pass\n\n\ndef test_b():\n    pass\n", encoding="utf-8")
    monkeypatch.setenv(env, "1")
    check = dr.run_tests("D1-TESTS", (str(suite),))
    assert check["passed"] and "2 passed" in check["detail"], check


def test_code_checks_count_a_real_skip_and_xfail(tmp_path):
    suite = tmp_path / "test_suite_skip_xfail.py"
    suite.write_text("import pytest\n\ndef test_a():\n    pass\n\n\n@pytest.mark.skip\ndef test_b():\n    pass\n\n\n"
                     "@pytest.mark.xfail\ndef test_c():\n    assert False\n", encoding="utf-8")
    check = dr.run_tests("D1-TESTS", (str(suite),))
    assert not check["passed"] and "skipped" in check["detail"] and "xfailed" in check["detail"], check


def test_code_checks_fail_without_pytest(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "pytest", None)
    check = dr.run_tests("D1-TESTS", ("tests/test_policy_gate.py",))
    assert not check["passed"] and "pytest" in check["detail"]


def test_the_predeclared_suites_include_every_gate_audit_and_coverage_test():
    assert {"tests/test_policy_gate.py", "tests/test_gate_audit_differential.py",
            "tests/test_gate_audit_typed_params.py", "tests/test_gate_canonicalizer_mutants.py"} <= set(dr.D1_TEST_FILES)
    assert {"tests/test_datamarking.py", "tests/test_defense_mutants.py"} <= set(dr.D2_TEST_FILES)


def test_make_target_omits_an_unset_window_so_the_report_fails_d2_context():
    import subprocess

    dry = subprocess.run(["make", "-n", "defense-readiness", "RUN=r"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    assert "--context-window" not in dry and "--output-reserve" not in dry
    dry = subprocess.run(["make", "-n", "defense-readiness", "RUN=r", "CONTEXT=200000", "RESERVE=20000"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    assert '--context-window "200000"' in dry and '--output-reserve "20000"' in dry


# --- Fix review of the November 9 lead push ---


def test_code_binding_allows_a_runner_fix_across_a_resumed_grid_and_later_report_code(tmp_path):
    """Decision 0028 item 5: a runner fix made during a resumed grid, or report code landing
    later in analysis/, isn't refused. Only what the suites exercise is bound."""
    from runner import paid_run

    root, run_dir = bound_repo(tmp_path)
    (root / "runner").mkdir()
    (root / "runner" / "execute.py").write_text("FIXED = True\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "runner fix, then resume")
    line = {"code_commit": _git(root, "rev-parse", "HEAD"),
            "code_digest": paid_run.code_digest(paid_run.code_hashes(root)), "dirty_paths": []}
    with (run_dir / "code_provenance.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    (root / "analysis").mkdir()
    (root / "analysis" / "report.py").write_text("REPORT = 1\n", encoding="utf-8")  # untracked report code
    ok, detail = dr.code_binding(run_dir, root=root)
    assert ok, detail


def test_code_binding_refuses_a_commit_that_is_not_a_full_object_name(tmp_path):
    root, run_dir = bound_repo(tmp_path)
    digest = json.loads((run_dir / "code_provenance.jsonl").read_text())["code_digest"]
    for commit in ("HEAD", "--output=x"):
        (run_dir / "code_provenance.jsonl").write_text(json.dumps({"code_commit": commit, "code_digest": digest}) + "\n",
                                                       encoding="utf-8")
        assert not dr.code_binding(run_dir, root=root)[0], commit
    assert not [p for p in root.iterdir() if p.name.startswith("x")]


def fake_repo(tmp_path, monkeypatch, tests):
    root = tmp_path / "fake"
    (root / "tests").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[tool.pytest.ini_options]\n", encoding="utf-8")
    for name, text in tests.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text, encoding="utf-8")
    monkeypatch.setattr(dr, "REPO_ROOT", root)
    return root


TWO = "def test_a():\n    pass\n\n\ndef test_b():\n    pass\n"


def test_code_checks_ignore_a_root_conftest_or_ini_that_drops_tests(tmp_path, monkeypatch):
    fake_repo(tmp_path, monkeypatch, {
        "conftest.py": "def pytest_collection_modifyitems(items):\n    del items[1:]\n",
        "pytest.ini": "[pytest]\naddopts = -k test_a\n",
        "tests/test_dropme.py": TWO,
    })
    check = dr.run_tests("D1-TESTS", ("tests/test_dropme.py",))
    assert check["passed"] and "2 passed" in check["detail"], check


def test_code_checks_count_a_module_level_skip(tmp_path, monkeypatch):
    fake_repo(tmp_path, monkeypatch, {
        "tests/test_kept.py": TWO,
        "tests/test_gone.py": "import pytest\npytest.importorskip('no_such_module_anywhere')\n\n\ndef test_c():\n    pass\n",
    })
    check = dr.run_tests("D1-TESTS", ("tests/test_kept.py", "tests/test_gone.py"))
    assert not check["passed"] and "skipped" in check["detail"], check


def test_code_checks_fail_a_run_that_exits_early(tmp_path, monkeypatch):
    fake_repo(tmp_path, monkeypatch, {
        "tests/test_exits.py": "import pytest\n\ndef test_a():\n    pass\n\n\ndef test_b():\n    pytest.exit('stop', returncode=0)\n\n\n"
                               "def test_c():\n    assert False\n",
    })
    check = dr.run_tests("D1-TESTS", ("tests/test_exits.py",))
    assert not check["passed"] and "not run" in check["detail"], check


def test_d1_denied_request_with_an_observed_effect_or_a_tool_result_event_is_not_ready():
    effect = tool_event(authorized=False, dispatched=False, blocked=True)
    effect["effect_observed"] = True
    assert "D1-NO-BLOCKED-DISPATCH" in failed(run(grid(**{D1: {"tool_events": [effect]}})), D1)

    trials = grid(**{D1: {"tool_events": [tool_event(authorized=False, dispatched=False, blocked=True)]}})
    i, record = find(trials, D1)
    log = trials[i][1]
    result_event = copy.deepcopy(log[-1])
    result_event.update(event_id=f"{record['logical_trial_id']}:tool", sequence=log[-1]["sequence"] + 1,
                        event_type="tool_result", model_call_id=None, attempt_id=None,
                        payload={"call_id": "c1", "step": 1, "observation": {}})
    trials[i] = (record, [*log, result_event])
    assert "D1-NO-BLOCKED-DISPATCH" in failed(run(trials), D1)
