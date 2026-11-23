"""The count-only Gate 4 audit (decision 0043 item 3, from decision 0042 item 9): pass or fail per
check, nothing else. The sweep and C1 have separate overall lines, and the exit code is the sweep's.

Every run here is a mock: a sweep from tests/test_sweep.py (a fake provider, no network) and a
C1 run through runner.execute with the C1 mock provider. Nothing reads results/ or an official
record.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import random
import re
import shutil
import sys
from pathlib import Path

import pytest

from analysis import report
from analysis.sanitizer import sanitize_bundle
from runner import c1_trial, execute, live_smoke
from runner import schedule as sched
from tests.test_sweep import SPEC, _run, corpus, frozen, provider  # noqa: F401  (fixtures)
from tests.test_verify_evidence import FakeAdapter

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "gate4_audit.py"
CHECKS = ("verify_sweep", "sanitized_match", "missingness", "model_comparability",
          "attempt_histories", "identifiers", "resets")
C1_CHECKS = ("c1_verify", "c1_sanitized_match", "c1_model_comparability", "c1_attempt_histories", "c1_identifiers",
             "c1_resets")
# Decision 0043 item 2: one line per headline comparison the report makes, under a fixed name.
HEADLINE = (
    "eligible_model_violation_rate_baseline", "eligible_model_violation_rate_policy_gate",
    "eligible_model_violation_rate_datamarking", "eligible_system_compromise_rate_baseline",
    "eligible_system_compromise_rate_policy_gate", "eligible_system_compromise_rate_datamarking",
    "eligible_clean_utility_baseline", "eligible_clean_utility_policy_gate", "eligible_clean_utility_datamarking",
    "eligible_high_risk_clean_utility_baseline", "eligible_high_risk_clean_utility_policy_gate",
    "eligible_high_risk_clean_utility_datamarking", "eligible_datamarking_attack_risk_difference",
    "eligible_datamarking_injection_specific_difference", "eligible_policy_gate_residual_system_risk_difference",
    "eligible_clean_utility_cost_policy_gate", "eligible_clean_utility_cost_datamarking",
)
LINE = re.compile(rf"^({'|'.join((*CHECKS, *HEADLINE, *C1_CHECKS, 'c1'))}): (pass|fail)$")
OVERALL = re.compile(r"^overall_(sweep|c1): (PASS|FAIL)$")
# Each name is a constant, the geometry, or a lookup that reads no outcome into a rate,
# estimate, interval, or difference (the reason for each is in the audit's docstring).
ALLOWED_REPORT_IMPORTS = {
    "THRESHOLD", "SECURITY", "UNIONS", "CONDITIONS", "BASELINE", "GATE", "MARKING", "ADAPTER_CONTRASTS",
    "Design", "design_from", "endpoint", "_index", "_keys", "_key_of", "_counts",
}
FORBIDDEN_REPORT_NAMES = {
    "rate", "defense_difference", "did", "condition_difference", "adapter_difference", "mixed_repeats",
    "outcome_decomposition", "reliability", "leave_one_family_out", "conformance", "block_reasons", "generate",
    "render", "bootstrap", "resamples", "percentile", "_estimate", "_values", "_sum", "_macro", "_rate_plan",
    "_paired_plan", "_defense_plan", "_did_plan", "_condition_plan", "_adapter_plan", "_primary_effects",
    "_plan_intervals", "_interval", "_Context", "_fill",
}
C1_IDS = ["c1-002", "c1-003", "c1-001", "c1-004"]  # F20's C1 prefix, as tests/test_c1_executor.py uses it
D0, D1, D2 = report.BASELINE, report.GATE, report.MARKING


def _load():
    if "gate4_audit" not in sys.modules:
        spec = importlib.util.spec_from_file_location("gate4_audit", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        sys.modules["gate4_audit"] = module
        spec.loader.exec_module(module)
    return sys.modules["gate4_audit"]


_CACHE: dict[str, Path] = {}


def _set_active(frozen, **changes):  # noqa: F811
    """Merge into this test's active.json, so the sweep and C1 fixtures can each add their part."""
    frozen.active.update(changes)
    frozen.path.write_text(json.dumps(frozen.active), encoding="utf-8")


def _copy(name: str, tmp_path: Path) -> Path:
    out = tmp_path / name
    shutil.copytree(_CACHE[name], out, symlinks=True)
    return out


@pytest.fixture
def run(gate, provider, corpus, tmp_path, tmp_path_factory):  # noqa: F811
    """One single-repeat mock sweep per session, copied into each test so tampering stays local."""
    if "sweep" not in _CACHE:
        gate.open()
        base = tmp_path_factory.mktemp("gate4-base") / "sweep"
        _run(provider, corpus, base)
        _CACHE["sweep"] = base
    return _copy("sweep", tmp_path)


@pytest.fixture
def run3(gate, provider, corpus, frozen, tmp_path, tmp_path_factory):  # noqa: F811
    """A three-repeat mock sweep (F20's run_indices): canaries, so fixture hashes, differ by repeat."""
    _set_active(frozen, run_indices=[1, 2, 3])
    if "sweep3" not in _CACHE:
        gate.open()
        base = tmp_path_factory.mktemp("gate4-run3") / "sweep3"
        _run(provider, corpus, base, spec={**SPEC, "repeats": 3})
        _CACHE["sweep3"] = base
    return _copy("sweep3", tmp_path)


class _Resolved:
    """The C1 mock, answering as the sweep's fake adapter resolves its model, so one model runs both."""

    def __init__(self, inner):
        self.inner = inner
        self.adapter_version = "fake-adapter-v0"
        self.request_settings = FakeAdapter.request_settings

    def complete(self, messages, tool_schemas, decoding, model_request):
        response = self.inner.complete(messages, tool_schemas, decoding, model_request)
        return {**response, "model_resolved": model_request["model"] + "-resolved"}


def _c1_spec():
    return sched.c1_schedule_spec(list(C1_IDS), experiment_id=SPEC["experiment_id"], model_id=SPEC["model_id"],
                                  seed=SPEC["seed"], protocol_sentinel=SPEC["protocol_sentinel"], repeats=3)


@pytest.fixture
def c1(provider, frozen, tmp_path, tmp_path_factory):  # noqa: F811
    """A mock C1 run on the sweep's experiment, model, seed, and sentinel: F20's four controls x three repeats."""
    _set_active(frozen, tier="F20", c1_controls=list(C1_IDS))
    if "c1" not in _CACHE:
        spec = _c1_spec()
        out = tmp_path_factory.mktemp("gate4-c1") / "c1"
        factory = c1_trial.provider_factory(c1_trial.C1_CORPUS_ROOT)
        execute.run_schedule(out, sched.generate_schedule(spec), spec=spec, delivery=True, split="c1_control",
                             protocol_version=frozen.active["protocol_version"], analysis_role="c1_control",
                             provider_factory=lambda trial, canaries: _Resolved(factory(trial, canaries)),
                             decoding=live_smoke.PROVIDERS["anthropic"]["decoding"])
        _CACHE["c1"] = out
    return _copy("c1", tmp_path)


def _overloaded(model_request):
    """An HTTP 529 with no model content: retried, and never a model the run resolved."""
    return {"outcome": "no_model_content", "provider_request_id": None, "model_requested": model_request["model"],
            "model_resolved": None, "provider_fingerprint": None, "raw_response": None,
            "usage": {"input_tokens": None, "output_tokens": None}, "provider_response": None,
            "requested_at": "2026-11-03T00:00:00Z", "completed_at": None, "latency_ms": None,
            "error": {"type": "InternalServerError", "status": 529, "provider_code": None,
                      "provider_type": "overloaded_error"}}


@pytest.fixture
def exhausted(gate, provider, corpus, monkeypatch, tmp_path, tmp_path_factory):  # noqa: F811
    """A mock sweep whose first trial's first call gets 529 on all three attempts: its retries run
    out, so it ends as an infrastructure failure whose record resolved no model."""
    if "exhausted" not in _CACHE:
        inner, calls = provider.adapter.complete, {"n": 0}

        def complete(messages, tool_schemas, decoding, model_request):
            calls["n"] += 1
            if calls["n"] <= 3:
                return _overloaded(model_request)
            return inner(messages, tool_schemas, decoding, model_request)

        gate.open()
        base = tmp_path_factory.mktemp("gate4-exhausted") / "exhausted"
        with monkeypatch.context() as patch:
            patch.setattr(provider.adapter, "complete", complete)
            _run(provider, corpus, base)
        _CACHE["exhausted"] = base
    return _copy("exhausted", tmp_path)


@pytest.fixture
def unbuilt(gate, provider, corpus, monkeypatch, tmp_path, tmp_path_factory):  # noqa: F811
    """A mock sweep in which one D1_POLICY_GATE trial's fixture build fails, so it starts with no
    fixture, database, render, or defense hash and never calls its provider."""
    if "unbuilt" not in _CACHE:
        real_prepare, real_build = execute.tool_delivery.prepare_case, execute.tool_delivery.build_fixtures
        state = {"cell": None, "failed": False}

        def prepare(base, channel, condition, configuration, template):
            state["cell"] = (channel, condition, configuration)
            return real_prepare(base, channel, condition, configuration, template)

        def build(*args, **kwargs):
            if not state["failed"] and state["cell"] == ("C3", "attack", D1):
                state["failed"] = True
                raise OSError("the fixture build failed")
            return real_build(*args, **kwargs)

        gate.open()
        base = tmp_path_factory.mktemp("gate4-unbuilt") / "unbuilt"
        with monkeypatch.context() as patch:
            patch.setattr(execute.tool_delivery, "prepare_case", prepare)
            patch.setattr(execute.tool_delivery, "build_fixtures", build)
            _run(provider, corpus, base)
        assert state["failed"]
        _CACHE["unbuilt"] = base
    return _copy("unbuilt", tmp_path)


@pytest.fixture
def bundle(run, tmp_path):
    out = tmp_path / "public"
    sanitize_bundle(run, out, commit="c", protocol_id="p")
    return out


@pytest.fixture
def c1_bundle(c1, tmp_path):
    out = tmp_path / "c1-public"
    sanitize_bundle(c1, out, commit="c", protocol_id="p")
    return out


def _spec_file(tmp_path: Path, spec: dict, name: str) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(spec), encoding="utf-8")
    return path


def _audit(capsys, run, bundle, frozen, corpus, *, c1=None, c1_bundle=None, spec=None, c1_spec=None):  # noqa: F811
    tmp = Path(frozen.path).parent
    argv = ["--raw", str(run), "--sanitized", str(bundle), "--active", str(frozen.path), "--corpus-root", str(corpus),
            "--sweep-spec", str(_spec_file(tmp, spec or SPEC, "sweep_spec.json")),
            "--c1-spec", str(_spec_file(tmp, c1_spec or _c1_spec(), "c1_spec.json"))]
    if c1 is not None:
        argv += ["--c1-raw", str(c1)]
    if c1_bundle is not None:
        argv += ["--c1-sanitized", str(c1_bundle)]
    code = _load().main(argv)
    captured = capsys.readouterr()
    return code, captured.out.splitlines(), captured.err


def _assert_only_tokens(lines, err, with_c1=True):
    """The sweep's checks, its eligibility lines in their fixed order, ``overall_sweep``, then C1's
    checks (or ``c1``) and ``overall_c1``: nothing else, and no digit in a value or an eligibility name."""
    assert err == ""
    assert all(LINE.match(line) or OVERALL.match(line) for line in lines)
    assert not any(ch.isdigit() for line in lines for ch in line.split(": ", 1)[1])
    assert not any(ch.isdigit() for slug in HEADLINE for ch in slug)
    names = [line.split(": ", 1)[0] for line in lines]
    end = names.index("overall_sweep")
    assert names[:len(CHECKS)] == list(CHECKS)
    eligible = names[len(CHECKS):end]
    assert eligible == [slug for slug in HEADLINE if slug in eligible]
    assert names[end + 1:] == (list(C1_CHECKS) if with_c1 else ["c1"]) + ["overall_c1"]


def _result(lines) -> dict[str, str]:
    return dict(line.split(": ", 1) for line in lines)


def _eligible(lines) -> dict[str, str]:
    return {name: value for name, value in _result(lines).items() if name.startswith("eligible_")}


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]


def _rewrite(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in records), encoding="utf-8")


def _loaded(run, frozen, corpus):  # noqa: F811
    audit = _load()
    return audit, audit.load(run, frozen.path, corpus)


def _started(data, record):
    return next(e for e in data.events[record["logical_trial_id"]] if e["event_type"] == "trial_started")["payload"]


# --------------------------------------------------------------------------- end to end


def test_a_clean_mock_sweep_and_c1_run_pass_every_check(capsys, run, bundle, c1, c1_bundle, frozen, corpus):
    code, lines, err = _audit(capsys, run, bundle, frozen, corpus, c1=c1, c1_bundle=c1_bundle)
    _assert_only_tokens(lines, err)
    result = _result(lines)
    assert [name for name in result if not name.startswith("eligible_")] == [
        *CHECKS, "overall_sweep", *C1_CHECKS, "overall_c1"]
    assert set(result.values()) == {"pass", "PASS"} and result["overall_sweep"] == result["overall_c1"] == "PASS"
    assert code == 0


def test_the_mock_sweep_prints_the_reports_headline_comparisons(capsys, run, bundle, c1, c1_bundle, frozen, corpus):
    _, lines, _ = _audit(capsys, run, bundle, frozen, corpus, c1=c1, c1_bundle=c1_bundle)
    table = {slug: (output_id, configuration) for slug, output_id, configuration in _load().HEADLINE}
    printed = {table[name] for name in _eligible(lines)}
    assert printed and printed == _report_headline(report.design_from(frozen.active, corpus))


def test_a_clean_three_repeat_sweep_passes_every_check(capsys, run3, c1, c1_bundle, frozen, corpus, tmp_path):
    bundle = tmp_path / "public3"
    sanitize_bundle(run3, bundle, commit="c", protocol_id="p")
    code, lines, err = _audit(capsys, run3, bundle, frozen, corpus, c1=c1, c1_bundle=c1_bundle,
                              spec={**SPEC, "repeats": 3})
    _assert_only_tokens(lines, err)
    assert set(_result(lines).values()) == {"pass", "PASS"} and _eligible(lines)
    assert code == 0


@pytest.mark.parametrize("given", ["neither", "raw only", "sanitized only"])
def test_without_both_c1_arguments_c1_fails_closed_and_the_sweep_stands(capsys, run, bundle, c1, c1_bundle, frozen,
                                                                       corpus, given):
    kwargs = {"raw only": {"c1": c1}, "sanitized only": {"c1_bundle": c1_bundle}}.get(given, {})
    code, lines, err = _audit(capsys, run, bundle, frozen, corpus, **kwargs)
    _assert_only_tokens(lines, err, with_c1=False)
    result = _result(lines)
    assert all(result[name] == "pass" for name in CHECKS) and result["overall_sweep"] == "PASS"
    assert lines[-2:] == ["c1: fail", "overall_c1: FAIL"]
    assert code == 0  # decision 0043 item 2: a C1 failure excludes C1 only


def test_a_tampered_bundle_fails_the_sweep_with_only_tokens_printed(capsys, run, bundle, c1, c1_bundle, frozen, corpus):
    path = next(bundle.glob("*/results.jsonl"))
    records = _jsonl(path)
    records[0]["security"]["system_compromise"] = not records[0]["security"]["system_compromise"]
    _rewrite(path, records)
    code, lines, err = _audit(capsys, run, bundle, frozen, corpus, c1=c1, c1_bundle=c1_bundle)
    _assert_only_tokens(lines, err)
    result = _result(lines)
    assert result["sanitized_match"] == "fail" and result["overall_sweep"] == "FAIL"
    assert result["overall_c1"] == "PASS" and code == 1


def test_a_missing_bundle_is_a_bare_fail_not_a_traceback(capsys, run, c1, c1_bundle, frozen, corpus, tmp_path):
    code, lines, err = _audit(capsys, run, tmp_path / "nowhere", frozen, corpus, c1=c1, c1_bundle=c1_bundle)
    _assert_only_tokens(lines, err)
    assert _result(lines)["sanitized_match"] == "fail" and code == 1


def test_no_digit_or_identifier_reaches_the_output(capsys, run, bundle, c1, c1_bundle, frozen, corpus):
    path = next(run.glob("*/results.jsonl"))
    records = _jsonl(path)
    records[0]["run_metadata"]["model_resolved"] = "another-model-0123456789"
    _rewrite(path, records)
    _, lines, err = _audit(capsys, run, bundle, frozen, corpus, c1=c1, c1_bundle=c1_bundle)
    _assert_only_tokens(lines, err)
    assert _result(lines)["overall_sweep"] == "FAIL"


def test_a_trial_whose_retries_ran_out_leaves_the_sweep_passing(capsys, exhausted, frozen, corpus, tmp_path):
    """Round 2's blocking finding: a correct run's infrastructure failure resolved no model. Every
    whole-sweep check passes, the comparisons that trial's cell enters print ineligible, and the
    exit code is the sweep's alone."""
    bundle = tmp_path / "exhausted-public"
    sanitize_bundle(exhausted, bundle, commit="c", protocol_id="p")
    code, lines, err = _audit(capsys, exhausted, bundle, frozen, corpus)
    _assert_only_tokens(lines, err, with_c1=False)
    result = _result(lines)
    assert {name: result[name] for name in CHECKS} == {name: "pass" for name in CHECKS}
    assert "fail" in _eligible(lines).values() and "pass" in _eligible(lines).values()
    assert result["overall_sweep"] == "PASS" and result["overall_c1"] == "FAIL" and code == 0


def test_a_system_exit_inside_a_check_prints_nothing(capsys, run, bundle, c1, c1_bundle, frozen, corpus, monkeypatch):
    audit = _load()

    def leak(_run):
        raise SystemExit("leaked value 0.0123")

    monkeypatch.setattr(audit, "check_identifiers", leak)
    code, lines, err = _audit(capsys, run, bundle, frozen, corpus, c1=c1, c1_bundle=c1_bundle)
    _assert_only_tokens(lines, err)
    result = _result(lines)
    assert result["identifiers"] == result["c1_identifiers"] == "fail" and code == 1
    assert result["overall_sweep"] == result["overall_c1"] == "FAIL"
    assert "0.0123" not in "\n".join(lines) + err


def test_a_keyboard_interrupt_still_stops_the_audit():
    audit = _load()

    def interrupted():
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        audit._safe(interrupted)
    assert audit._safe(lambda: (_ for _ in ()).throw(GeneratorExit("x"))) is False


# --------------------------------------------------------------------------- verify_sweep


def test_verify_sweep_fails_when_a_scheduled_trial_is_missing(run, frozen, corpus):
    victim = next(run.glob("*/results.jsonl")).parent
    shutil.rmtree(victim)
    audit = _load()
    assert audit.check_verify_sweep(run, corpus, frozen.active, SPEC) is False


def test_verify_sweep_fails_when_the_run_is_not_the_committed_spec(run, frozen, corpus):
    audit = _load()
    assert audit.check_verify_sweep(run, corpus, frozen.active, SPEC) is True
    assert audit.check_verify_sweep(run, corpus, frozen.active, {**SPEC, "seed": "another-seed"}) is False
    other = {**frozen.active, "base_case_ids": ["eval-902"]}
    assert audit.check_verify_sweep(run, corpus, other, SPEC) is False


# --------------------------------------------------------------------------- sanitized_match


def test_sanitized_match_fails_when_a_released_file_differs_from_its_manifest(run, bundle):
    audit = _load()
    assert audit.check_sanitized_match(run, bundle) is True
    path = next(bundle.glob("*/events.jsonl"))
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert audit.check_sanitized_match(run, bundle) is False


def test_sanitized_match_fails_when_a_record_is_not_the_sanitizer_output(run, bundle):
    audit = _load()
    path = next(bundle.glob("*/results.jsonl"))
    records = _jsonl(path)
    records[0]["final_output"] = "something the sanitizer would never write"
    _rewrite(path, records)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        data = (bundle / entry["path"]).read_bytes()
        entry["sha256"], entry["size_bytes"] = hashlib.sha256(data).hexdigest(), len(data)
    (bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert audit.check_sanitized_match(run, bundle) is False


@pytest.mark.parametrize("stray", ["notes.txt", "code_provenance.jsonl", "extra/results.jsonl.bak", "canaries.json"])
def test_sanitized_match_fails_on_a_file_the_manifest_does_not_list(run, bundle, stray):
    audit = _load()
    target = bundle / stray if "/" in stray else next(bundle.glob("*/results.jsonl")).parent / stray
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}\n", encoding="utf-8")
    assert audit.check_sanitized_match(run, bundle) is False


def test_sanitized_match_fails_on_a_stray_file_at_the_bundle_root(run, bundle):
    audit = _load()
    (bundle / "README").write_text("hello\n", encoding="utf-8")
    assert audit.check_sanitized_match(run, bundle) is False


def test_sanitized_match_fails_on_a_listed_file_that_is_missing(run, bundle):
    audit = _load()
    next(bundle.glob("*/events.jsonl")).unlink()
    assert audit.check_sanitized_match(run, bundle) is False


# --------------------------------------------------------------------------- missingness accounting on the mock run


def test_missingness_checks_the_accounting_not_the_threshold(run, frozen, corpus):
    """Decision 0043 item 2: a recorded null is accounted for; the threshold is eligibility's."""
    audit, data = _loaded(run, frozen, corpus)
    assert audit.check_missingness(data) is True
    for record in data.records:
        record["security"]["system_compromise"] = None
        record["utility"]["pass"] = None
    assert audit.check_missingness(data) is True


def test_missingness_fails_on_a_planned_cell_with_no_record(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    data.records.pop()
    assert audit.check_missingness(data) is False


def test_missingness_fails_on_a_record_outside_the_primary_set(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    data.records.append({**data.records[0], "split": "development"})
    assert audit.check_missingness(data) is False
    audit, data = _loaded(run, frozen, corpus)
    data.records[0] = {**data.records[0], "analysis_role": "c1_control"}
    assert audit.check_missingness(data) is False


def test_missingness_passes_a_three_repeat_run(run3, frozen, corpus):
    audit, data = _loaded(run3, frozen, corpus)
    assert audit.check_missingness(data) is True


def test_eligibility_on_the_mock_run_follows_the_null_cell(run, frozen, corpus):
    """One null attacked D0_BASELINE model_violation leaves exactly the headline comparisons that
    read it: the baseline rate and both D2_DATAMARKING differences."""
    audit, data = _loaded(run, frozen, corpus)
    planned = audit.planned_headline(data.design)
    assert planned and all(audit.check_eligible(data, slug) for slug in planned)
    victim = next(r for r in data.records if r["condition"] == "attack" and r["configuration"] == D0)
    victim["security"]["model_violation"] = None
    assert audit.check_missingness(data) is True
    assert {slug for slug in planned if not audit.check_eligible(data, slug)} == {
        "eligible_model_violation_rate_baseline", "eligible_datamarking_attack_risk_difference",
        "eligible_datamarking_injection_specific_difference"}


def test_eligibility_of_a_comparison_the_geometry_does_not_plan_fails(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    assert audit.check_eligible(data, "eligible_not_a_comparison") is False
    narrow = report.Design(data.design.base_case_ids, data.design.channels, (D0,), data.design.run_indices,
                           data.design.templates, data.design.high_risk, data.design.families)
    assert "eligible_clean_utility_cost_datamarking" not in audit.planned_headline(narrow)


# --------------------------------------------------------------------------- eligibility against the report


SECURITY_UNIONS = ("model_violation", "system_compromise")


def _design(bases=20, runs=(1, 2, 3), channels=("C2", "C3", "C4"), configurations=(D0, D1, D2), templates=2,
            high_risk=("t0",)):
    ids = tuple(f"eval-{i:03d}" for i in range(bases))
    return report.Design(ids, tuple(channels), tuple(configurations), tuple(runs),
                         {b: f"t{i % templates}" for i, b in enumerate(ids)}, frozenset(high_risk), {b: "f" for b in ids})


def _records(design, value=False):
    return [{"split": "evaluation", "analysis_role": "primary_indirect", "logical_trial_id": f"{b}:{ch}:{k}:{g}:{r}",
             "base_case_id": b, "channel": ch, "condition": k, "configuration": g, "run_index": r,
             "security": {name: value for name in report.SECURITY}, "utility": {"pass": None if value is None else True}}
            for b in design.base_case_ids for ch in design.channels for k in report.CONDITIONS
            for g in design.configurations for r in design.run_indices]


def _null(records, name, cells):
    for record in records:
        if (record["base_case_id"], record["channel"], record["condition"], record["configuration"],
                record["run_index"]) in cells:
            if name == "utility_pass":
                record["utility"]["pass"] = None
            else:
                record["security"][name] = None


def _synthetic(design, records):
    return _load().Run(records, {}, {}, design)


def _report_ineligible(records, design) -> set:
    """The report's own headline exclusions, read from its generated notes: ``(output ID,
    configuration or None)`` for each comparison it says leaves the headline."""
    found = set()
    for section in report.generate(records, design, {}, draws=10)["sections"]:
        for note in section.notes:
            if "leaves the headline" in note:
                label = note.split(" in ", 1)[1].split(" / ", 1)[0]
                found.add((section.output_id, label if label in design.configurations else None))
    return found


def _report_headline(design) -> set:
    """Every headline comparison the report makes over this geometry: with every endpoint
    missing, each one it makes says it leaves the headline."""
    return _report_ineligible(_records(design, value=None), design)


def _audit_ineligible(design, records) -> set:
    audit = _load()
    table = {slug: (output_id, configuration) for slug, output_id, configuration in audit.HEADLINE}
    data = _synthetic(design, records)
    return {table[slug] for slug in audit.planned_headline(design) if not audit.check_eligible(data, slug)}


def test_the_headline_names_are_fixed():
    assert tuple(slug for slug, _, _ in _load().HEADLINE) == HEADLINE


@pytest.mark.parametrize("design", [
    _design(), _design(configurations=(D0,)), _design(configurations=(D0, D2)), _design(configurations=(D0, D1)),
    _design(configurations=(D1, D2)), _design(channels=("C2",)), _design(high_risk=()), _design(templates=1),
], ids=["full", "baseline", "datamarking", "policy-gate", "no-baseline", "one-adapter", "no-high-risk", "one-task"])
def test_b2_the_audit_plans_exactly_the_reports_headline_comparisons(design):
    audit = _load()
    table = {slug: (output_id, configuration) for slug, output_id, configuration in audit.HEADLINE}
    assert {table[slug] for slug in audit.planned_headline(design)} == _report_headline(design)


def test_b2_three_plus_three_missing_leaves_only_the_four_cell_difference():
    """Each two-arm comparison is at exactly 5%, but the four-cell difference is at 10%."""
    design = _design(channels=("C2",), configurations=(D0, D2), templates=1)
    records = _records(design)
    _null(records, "model_violation", {(f"eval-{i:03d}", "C2", "attack", D2, 1) for i in (0, 1, 2)})
    _null(records, "model_violation", {(f"eval-{i:03d}", "C2", "clean", D0, 1) for i in (3, 4, 5)})
    assert report.did(records, design).over_threshold is True
    assert _audit_ineligible(design, records) == {("DatamarkingInjectionSpecificDifference", None)}
    assert _audit_ineligible(design, records) == _report_ineligible(records, design)
    assert _load().check_missingness(_synthetic(design, records)) is True


def test_b2_secondary_comparisons_leave_no_headline_comparison():
    """Round 2: the report applies no headline rule to the six facts, to secure task completion,
    to the background rates, or to the adapter contrasts, so nor does the audit."""
    design = _design(channels=("C2", "C3"), configurations=(D0,), templates=1)
    records = _records(design)
    for fact in report.FACTS:
        _null(records, fact, {(b, ch, k, D0, 1) for b in design.base_case_ids for ch in design.channels
                              for k in report.CONDITIONS})
    _null(records, "system_compromise", {(b, ch, "clean", D0, r) for b in design.base_case_ids
                                         for ch in design.channels for r in design.run_indices})
    _null(records, "utility_pass", {(b, ch, "attack", D0, r) for b in design.base_case_ids
                                    for ch in design.channels for r in design.run_indices})
    # each adapter misses 5% on different keys, so the C2 - C3 contrast misses 10%
    _null(records, "model_violation", {(f"eval-{i:03d}", "C2", "attack", D0, 1) for i in (0, 1, 2)})
    _null(records, "model_violation", {(f"eval-{i:03d}", "C3", "attack", D0, 1) for i in (3, 4, 5)})
    assert report.adapter_difference(records, design, first="C2", second="C3").over_threshold is True
    assert _report_ineligible(records, design) == set() == _audit_ineligible(design, records)


@pytest.mark.parametrize("runs, missing, passes", [
    ((1, 2, 3), 3, True),       # 3 of 60 keys: exactly 5%
    ((1, 2, 3), 4, False),      # 4 of 60: just over
    ((1, 2, 3, 4, 5), 5, True),   # 5 of 100: exactly 5%
    ((1, 2, 3, 4, 5), 6, False),  # 6 of 100: just over
])
def test_b2_the_threshold_boundary(runs, missing, passes):
    design = _design(runs=runs, channels=("C2",), configurations=(D0,), templates=1)
    records = _records(design)
    cells = [(b, "C2", "attack", D0, r) for r in runs for b in design.base_case_ids][:missing]
    _null(records, "model_violation", set(cells))
    expected = set() if passes else {("ModelViolationRate", D0)}
    assert _report_ineligible(records, design) == expected == _audit_ineligible(design, records)


@pytest.mark.parametrize("seed", range(40))
def test_b2_the_audit_decides_eligibility_exactly_as_the_report_does(seed):
    rng = random.Random(seed)
    design = _design()
    records = _records(design)
    channel, configuration, condition = (rng.choice(design.channels), rng.choice(design.configurations),
                                         rng.choice(report.CONDITIONS))
    for _ in range(rng.randrange(0, 5)):
        name = rng.choice((*SECURITY_UNIONS, "utility_pass", "external_exfiltration"))
        cells = set()
        for _ in range(rng.randrange(1, 5)):
            spread = rng.random() < 0.3
            cells.add((rng.choice(design.base_case_ids), rng.choice(design.channels) if spread else channel,
                       rng.choice(report.CONDITIONS) if spread else condition,
                       rng.choice(design.configurations) if spread else configuration, rng.choice(design.run_indices)))
        _null(records, name, cells)
    for _ in range(rng.randrange(0, 3)):
        records.pop(rng.randrange(len(records)))
    assert _audit_ineligible(design, records) == _report_ineligible(records, design)


def test_b2_a_geometry_with_nothing_planned_fails():
    audit = _load()
    for design in (_design(runs=()), _design(bases=0), _design(channels=()), _design(configurations=())):
        data = _synthetic(design, _records(design))
        assert audit.check_missingness(data) is False
        assert not any(audit._safe(lambda slug=slug: audit.check_eligible(data, slug))
                       for slug in audit.planned_headline(design))


def test_b2_a_cell_outside_the_geometry_fails():
    design = _design(channels=("C2",), configurations=(D0,), templates=1)
    records = _records(design)
    records.append({**records[0], "channel": "C3"})
    audit = _load()
    data = _synthetic(design, records)
    assert audit._safe(lambda: audit.check_missingness(data)) is False
    assert not any(audit._safe(lambda slug=slug: audit.check_eligible(data, slug))
                   for slug in audit.planned_headline(design))


# --------------------------------------------------------------------------- model_comparability


def test_model_comparability_fails_on_a_second_resolved_model(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    assert audit.check_model_comparability(data) is True
    data.records[0]["model_calls"][0]["model_resolved"] = "another-model"
    assert audit.check_model_comparability(data) is False


def test_model_comparability_fails_on_a_changed_fingerprint(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    data.records[0]["model_calls"][0]["provider_fingerprint"] = "fp-a"
    data.records[1]["model_calls"][0]["provider_fingerprint"] = "fp-b"
    assert audit.check_model_comparability(data) is False


def test_model_comparability_fails_on_mixed_code_or_decoding(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    data.records[0]["run_metadata"]["code_commit"] = "0" * 40
    assert audit.check_model_comparability(data) is False
    audit, data = _loaded(run, frozen, corpus)
    _started(data, data.records[0])["decoding"]["effort"] = "high"
    assert audit.check_model_comparability(data) is False


@pytest.mark.parametrize("field", ["code_commit", "corpus_hash", "schedule_seed"])
def test_model_comparability_fails_on_a_field_null_everywhere(run, frozen, corpus, field):
    audit, data = _loaded(run, frozen, corpus)
    for record in data.records:
        record["run_metadata"][field] = None
    assert audit.check_model_comparability(data) is False


def test_model_comparability_takes_one_corpus_hash_per_base(run, c1, frozen):
    """The corpus hash is each base's own, so a run of several bases (here C1's four) has several."""
    audit = _load()
    data = audit.load(c1, frozen.path)
    assert len({r["run_metadata"]["corpus_hash"] for r in data.records}) == len(C1_IDS)
    assert audit.check_model_comparability(data) is True
    record = next(r for r in data.records if r["run_index"] == 2)
    record["run_metadata"]["corpus_hash"] = "0" * 64
    assert audit.check_model_comparability(data) is False


def test_model_comparability_fails_on_a_trial_start_field_null_everywhere(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    for record in data.records:
        _started(data, record)["max_steps"] = None
    assert audit.check_model_comparability(data) is False


def test_model_comparability_fails_on_a_defense_without_its_hash(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    for record in data.records:
        if record["configuration"] == D2:
            record["run_metadata"]["defense_hash"] = None
    assert audit.check_model_comparability(data) is False


def test_model_comparability_fails_against_active_json(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    data.active["empirical"]["model_resolved"] = "not-what-ran"
    assert audit.check_model_comparability(data) is False


def test_model_comparability_passes_a_trial_whose_retries_ran_out(exhausted, frozen, corpus):
    """Round 2's blocking finding: the trial's attempts never returned a model, so its record's
    resolved model is null (runner/mock_slice.py's ``_resolved_model``), and it has no model call."""
    audit, data = _loaded(exhausted, frozen, corpus)
    [failed] = [r for r in data.records if r["status"] != "completed"]
    assert failed["status"] == "infrastructure_failure" and failed["run_metadata"]["model_resolved"] is None
    assert failed["model_calls"] == [] and all(a["outcome"] == "no_model_content" for a in failed["attempts"])
    assert audit.check_model_comparability(data) is True
    assert audit.check_attempt_histories(data) is True and audit.check_identifiers(data) is True
    assert audit.check_resets(data) is True


def test_model_comparability_still_fails_on_a_second_resolved_model_beside_a_null(exhausted, frozen, corpus):
    audit, data = _loaded(exhausted, frozen, corpus)
    completed = next(r for r in data.records if r["status"] == "completed")
    completed["run_metadata"]["model_resolved"] = "another-model"
    assert audit.check_model_comparability(data) is False
    audit, data = _loaded(exhausted, frozen, corpus)
    next(r for r in data.records if r["status"] == "completed")["model_calls"][0]["model_resolved"] = "another-model"
    assert audit.check_model_comparability(data) is False


def test_model_comparability_fails_when_no_model_resolved_anywhere(exhausted, frozen, corpus):
    audit, data = _loaded(exhausted, frozen, corpus)
    for record in data.records:
        record["run_metadata"]["model_resolved"] = None
        for call in record["model_calls"]:
            call["model_resolved"] = None
    assert audit.check_model_comparability(data) is False


def test_model_comparability_passes_a_trial_whose_fixture_build_failed(unbuilt, frozen, corpus):
    """That trial's defense started with no hash; a null is allowed only on an infrastructure failure."""
    audit, data = _loaded(unbuilt, frozen, corpus)
    [failed] = [r for r in data.records if r["status"] != "completed"]
    assert failed["status"] == "infrastructure_failure" and failed["configuration"] == D1
    assert failed["run_metadata"]["defense_hash"] is None and failed["model_calls"] == []
    assert audit.check_model_comparability(data) is True
    failed["status"] = "completed"
    assert audit.check_model_comparability(data) is False


# --------------------------------------------------------------------------- attempt_histories


def test_attempt_histories_fail_on_a_retry_after_model_content(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    assert audit.check_attempt_histories(data) is True
    record = data.records[0]
    first = record["attempts"][0]
    retry = {**first, "attempt_index": 2, "attempt_id": first["model_call_id"] + ":a2"}
    record["attempts"].insert(1, retry)  # a1 had model content, so a2 is a forbidden retry
    assert audit.check_attempt_histories(data) is False


def test_attempt_histories_fail_past_three_attempts(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    record = data.records[0]
    call = record["attempts"][0]["model_call_id"]
    empty = [{**record["attempts"][0], "attempt_index": i, "attempt_id": f"{call}:a{i}", "outcome": "no_model_content"}
             for i in (1, 2, 3)]
    record["attempts"][0:1] = empty + [{**record["attempts"][0], "attempt_index": 4, "attempt_id": f"{call}:a4"}]
    assert audit.check_attempt_histories(data) is False


def test_attempt_histories_fail_with_no_records(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    data.records.clear()
    assert audit.check_attempt_histories(data) is False


# --------------------------------------------------------------------------- identifiers


def test_identifiers_fail_on_a_broken_suffix(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    assert audit.check_identifiers(data) is True
    data.records[0]["model_calls"][0]["model_call_id"] += "x"
    assert audit.check_identifiers(data) is False


def test_identifiers_fail_on_an_event_sequence_gap(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    trial = data.records[0]["logical_trial_id"]
    del data.events[trial][2]
    assert audit.check_identifiers(data) is False


def test_identifiers_fail_on_a_trial_id_that_does_not_bind_its_cell(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    data.records[0]["channel"] = "C3" if data.records[0]["channel"] != "C3" else "C2"
    assert audit.check_identifiers(data) is False


def test_identifiers_take_the_sentinel_from_the_spec_not_the_version(run, frozen, corpus):
    """The official specs' sentinel is canary-2026-v1, which no protocol version spells."""
    audit, data = _loaded(run, frozen, corpus)
    data.active["protocol_version"] = "9.9.9"
    assert audit.check_identifiers(data) is True
    data.stored_spec["protocol_sentinel"] = "another-sentinel"
    assert audit.check_identifiers(data) is False


def test_identifiers_fail_on_the_unfrozen_sentinel(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    data.stored_spec["protocol_sentinel"] = sched.PROTOCOL_SENTINEL
    assert audit.check_identifiers(data) is False


# --------------------------------------------------------------------------- resets


def test_resets_pass_across_repeats_whose_canaries_differ(run3, frozen, corpus):
    audit, data = _loaded(run3, frozen, corpus)
    fixtures = {(r["base_case_id"], r["channel"], r["condition"]): set() for r in data.records}
    for record in data.records:
        fixtures[(record["base_case_id"], record["channel"], record["condition"])].add(
            _started(data, record)["fixture_hash"])
    assert all(len(hashes) == 3 for hashes in fixtures.values())  # one per repeat: the canaries are in the files
    assert audit.check_resets(data) is True


def _superblock_cell(data, run_index, channel, condition):
    return [r for r in data.records if r["run_index"] == run_index and r["channel"] == channel
            and r["condition"] == condition]


def test_resets_fail_when_a_repeat_starts_from_another_database(run3, frozen, corpus):
    audit, data = _loaded(run3, frozen, corpus)
    for record in _superblock_cell(data, 2, "C2", "attack"):  # every configuration, so the superblock agrees
        _started(data, record)["database_hash"] = "0" * 64
    assert audit.check_resets(data) is False


def test_resets_fail_when_a_repeat_starts_from_another_render(run3, frozen, corpus):
    audit, data = _loaded(run3, frozen, corpus)
    for record in _superblock_cell(data, 3, "C3", "clean"):
        _started(data, record)["rendered_sha256"] = "0" * 64
        record["run_metadata"]["rendered_fixture_hash"] = "0" * 64
    assert audit.check_resets(data) is False


def test_resets_fail_when_one_configuration_starts_from_other_fixtures(run3, frozen, corpus):
    audit, data = _loaded(run3, frozen, corpus)
    record = next(r for r in _superblock_cell(data, 2, "C4", "attack") if r["configuration"] == D1)
    _started(data, record)["fixture_hash"] = "0" * 64
    assert audit.check_resets(data) is False


def test_resets_fail_when_attack_and_clean_do_not_share_their_superblock_canaries(run3, frozen, corpus):
    audit, data = _loaded(run3, frozen, corpus)
    other = next(r for r in data.records if r["run_index"] == 1)["canaries"]
    for record in _superblock_cell(data, 2, "C2", "clean"):
        record["canaries"] = list(other)
    assert audit.check_resets(data) is False


def test_resets_fail_when_two_superblocks_reuse_one_canary_pair(run3, frozen, corpus):
    audit, data = _loaded(run3, frozen, corpus)
    canaries = json.loads((run3 / execute.CANARIES_FILE).read_text(encoding="utf-8"))
    first = next(r for r in data.records if r["run_index"] == 1)
    second = next(r for r in data.records if r["run_index"] == 2)
    canaries[second["comparison_superblock_id"]]["canaries"] = list(first["canaries"])
    for record in data.records:
        if record["comparison_superblock_id"] == second["comparison_superblock_id"]:
            record["canaries"] = list(first["canaries"])
    data.canary_map = canaries
    assert audit.check_resets(data) is False


def test_resets_fail_when_a_trial_started_from_a_different_state(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    assert audit.check_resets(data) is True
    _started(data, data.records[0])["database_hash"] = "0" * 64
    assert audit.check_resets(data) is False


def test_resets_fail_when_the_record_and_its_trial_start_disagree(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    data.records[0]["run_metadata"]["rendered_fixture_hash"] = "0" * 64
    assert audit.check_resets(data) is False


def test_resets_fail_with_no_records(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    data.records.clear()
    assert audit.check_resets(data) is False


def test_resets_allow_no_starting_state_only_on_an_infrastructure_failure(unbuilt, frozen, corpus):
    audit, data = _loaded(unbuilt, frozen, corpus)
    [failed] = [r for r in data.records if r["status"] != "completed"]
    assert _started(data, failed)["fixture_hash"] is None
    assert audit.check_resets(data) is True
    failed["status"] = "completed"
    assert audit.check_resets(data) is False


def test_resets_fail_on_a_null_fixture_hash_on_a_completed_trial(run, frozen, corpus):
    audit, data = _loaded(run, frozen, corpus)
    _started(data, data.records[0])["fixture_hash"] = None
    assert audit.check_resets(data) is False


def test_resets_still_check_the_canaries_of_an_infrastructure_failure(unbuilt, frozen, corpus):
    audit, data = _loaded(unbuilt, frozen, corpus)
    failed = next(r for r in data.records if r["status"] != "completed")
    failed["canaries"] = ["not-its-superblock-pair"]
    assert audit.check_resets(data) is False


# --------------------------------------------------------------------------- C1


def test_c1_verify_fails_when_a_scheduled_c1_trial_is_missing(c1, frozen):
    audit = _load()
    assert audit.check_c1_verify(c1, frozen.active, _c1_spec()) is True
    shutil.rmtree(next(c1.glob("*/results.jsonl")).parent)
    assert audit.check_c1_verify(c1, frozen.active, _c1_spec()) is False


@pytest.mark.parametrize("change", [
    {"c1_controls": ["c1-002", "c1-003", "c1-001"]},
    {"c1_controls": ["c1-003", "c1-002", "c1-001", "c1-004"]},
    {"tier": "NOPE"},
])
def test_c1_verify_fails_when_the_c1_run_is_not_active_jsons_c1_schedule(c1, frozen, change):
    audit = _load()
    assert audit.check_c1_verify(c1, {**frozen.active, **change}, _c1_spec()) is False


def test_c1_verify_fails_when_the_c1_run_is_not_the_committed_c1_spec(c1, frozen):
    audit = _load()
    assert audit.check_c1_verify(c1, frozen.active, {**_c1_spec(), "seed": "another"}) is False


def test_c1_sanitized_match_fails_on_a_tampered_or_stray_file(c1, c1_bundle):
    audit = _load()
    assert audit.check_sanitized_match(c1, c1_bundle) is True
    (c1_bundle / "stray.jsonl").write_text("{}\n", encoding="utf-8")
    assert audit.check_sanitized_match(c1, c1_bundle) is False


def test_c1_model_comparability_fails_when_c1_ran_another_model(run, c1, frozen, corpus):
    audit = _load()
    sweep_data, c1_data = audit.load(run, frozen.path, corpus), audit.load(c1, frozen.path)
    assert audit.check_c1_model_comparability(c1_data, sweep_data) is True
    for record in c1_data.records:
        record["run_metadata"]["model_resolved"] = "another-model"
        for call in record["model_calls"]:
            call["model_resolved"] = "another-model"
    assert audit.check_c1_model_comparability(c1_data, sweep_data) is False
    assert audit.check_c1_model_comparability(audit.load(c1, frozen.path), None) is False


def test_c1_model_comparability_fails_on_another_code_commit(run, c1, frozen, corpus):
    audit = _load()
    sweep_data, c1_data = audit.load(run, frozen.path, corpus), audit.load(c1, frozen.path)
    for record in c1_data.records:
        record["run_metadata"]["code_commit"] = "0" * 40
    assert audit.check_c1_model_comparability(c1_data, sweep_data) is False


def test_c1_identifiers_and_attempt_histories(c1, frozen):
    audit = _load()
    data = audit.load(c1, frozen.path)
    assert audit.check_identifiers(data) is True and audit.check_attempt_histories(data) is True
    data.records[0]["attempts"][0]["attempt_id"] += "x"
    assert audit.check_identifiers(data) is False


def test_c1_resets_pass_and_fail_like_the_sweeps(c1, frozen):
    """C1 records carry the reset fields (runner/execute.py builds C1 fixtures and a database), but
    a C1 control has no rendered fixture, so its render hash is null on every trial."""
    audit = _load()
    data = audit.load(c1, frozen.path)
    assert all(_started(data, r)["rendered_sha256"] is None for r in data.records)
    assert audit.check_c1_resets(data) is True
    assert audit.check_resets(data) is False  # the sweep's rule wants a render
    record = next(r for r in data.records if r["run_index"] == 2)
    _started(data, record)["database_hash"] = "0" * 64
    assert audit.check_c1_resets(data) is False


def test_c1_resets_fail_when_two_superblocks_reuse_one_canary_pair(c1, frozen):
    audit = _load()
    data = audit.load(c1, frozen.path)
    first = next(r for r in data.records if r["run_index"] == 1)
    second = next(r for r in data.records if r["run_index"] == 2 and r["base_case_id"] == first["base_case_id"])
    data.canary_map[second["comparison_superblock_id"]]["canaries"] = list(first["canaries"])
    second["canaries"] = list(first["canaries"])
    assert audit.check_c1_resets(data) is False


def test_c1_resets_fail_on_a_recorded_render_or_a_missing_fixture(c1, frozen):
    audit = _load()
    data = audit.load(c1, frozen.path)
    _started(data, data.records[0])["rendered_sha256"] = "0" * 64
    data.records[0]["run_metadata"]["rendered_fixture_hash"] = "0" * 64
    assert audit.check_c1_resets(data) is False
    data = audit.load(c1, frozen.path)
    _started(data, data.records[0])["fixture_hash"] = None
    assert audit.check_c1_resets(data) is False


def test_c1_model_comparability_ignores_a_trial_that_resolved_no_model(run, c1, frozen, corpus):
    audit = _load()
    sweep_data, c1_data = audit.load(run, frozen.path, corpus), audit.load(c1, frozen.path)
    c1_data.records[0]["run_metadata"]["model_resolved"] = None
    for call in c1_data.records[0]["model_calls"]:
        call["model_resolved"] = None
    assert audit.check_c1_model_comparability(c1_data, sweep_data) is True


def test_a_tampered_c1_run_fails_only_c1_end_to_end(capsys, run, bundle, c1, c1_bundle, frozen, corpus):
    path = next(c1_bundle.glob("*/results.jsonl"))
    records = _jsonl(path)
    records[0]["status"] = "infrastructure_failure"
    _rewrite(path, records)
    code, lines, err = _audit(capsys, run, bundle, frozen, corpus, c1=c1, c1_bundle=c1_bundle)
    _assert_only_tokens(lines, err)
    result = _result(lines)
    assert result["c1_sanitized_match"] == "fail" and result["overall_c1"] == "FAIL"
    assert result["overall_sweep"] == "PASS" and code == 0  # a C1 failure excludes C1 only


def test_a_sweep_failure_fails_the_exit_code_whatever_c1_says(capsys, run, bundle, c1, c1_bundle, frozen, corpus):
    next(bundle.glob("*/events.jsonl")).unlink()
    code, lines, err = _audit(capsys, run, bundle, frozen, corpus, c1=c1, c1_bundle=c1_bundle)
    _assert_only_tokens(lines, err)
    assert _result(lines)["overall_sweep"] == "FAIL" and _result(lines)["overall_c1"] == "PASS" and code == 1


# --------------------------------------------------------------------------- what it may import


def test_the_audit_imports_no_estimate_from_the_report():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "analysis.report":
            names |= {alias.name for alias in node.names}
        if isinstance(node, ast.ImportFrom) and node.module == "analysis":
            assert all(alias.name != "report" for alias in node.names)
        if isinstance(node, ast.Import):
            assert all(alias.name != "analysis.report" for alias in node.names)
        if isinstance(node, (ast.Attribute, ast.Name)):
            name = node.attr if isinstance(node, ast.Attribute) else node.id
            assert name not in FORBIDDEN_REPORT_NAMES, f"the audit reaches {name}"
    assert names == ALLOWED_REPORT_IMPORTS


def test_the_audit_prints_through_one_emitter():
    source = SCRIPT.read_text(encoding="utf-8")
    assert source.count("print(") == 1


def test_the_header_cites_decision_0043_item_3_and_its_origin():
    header = ast.get_docstring(ast.parse(SCRIPT.read_text(encoding="utf-8"))).split("\n\n", 1)[0]
    assert "decision 0043 item 3" in header and "decision 0042 item 9" in header
