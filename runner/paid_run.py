"""The paid-run gate (decision 0023): no paid model call without the lead's record.

Every non-mock provider, on every runner path, passes ``require_paid_run``
before its first call. It refuses unless all of these hold:

* the run isn't in CI and no provider variable is set in the environment
  (keys come only from the env file the runner reads itself, decision 0010);
* every tool process runs in the sandbox (``tools.sandbox``), which refuses on
  an unsupported platform, a missing sandbox binary, or a root user;
* the provider declares decision 0026 item 3's one-call setting;
* ``protocol/paid_run_record.json`` exists, validates against its schema, is
  committed and unchanged, names a commit on this history, and is dated between
  that commit and today;
* the running sandbox is the one the record's mock grid ran under, so the paid
  run uses the same platform and sandbox mode as its preflight;
* the code the paid run executes is the code the record pinned: no hashed path is
  uncommitted, untracked, or ignored, apart from ``.DS_Store`` and ``__pycache__``
  bytecode Python wouldn't load or that matches its source, and every tracked hashed
  file's SHA-256 equals the record's;
* the installed packages and Python are the record's, at the versions ``uv.lock`` pins;
* the mock grid the record names is still in this checkout, matches the record's
  digests, and passes every check ``build_record`` makes, because no digest in a
  file anyone can write proves a run happened;
* ``runner.spend_ledger`` finds its ledger and cap, spend plus one trial's bound
  within the cap, and trials within SPEC.md Section 9's ceiling.

The record itself is bound to its preflight: every run writes the code it ran
to ``code_provenance.jsonl`` when each invocation starts and stops, and
``build_record`` refuses unless every invocation of the mock grid ran this
checkout's hashed code, clean, with tool-result delivery, on its committed corpus
and spec, and the task worked in every cell.

The one exception is the project lead's live smoke (``make live-smoke``, TASKS.md
paid-run condition), which needs no record. It still runs its read tool in the
sandbox, from clean, locked code, and inside the ledger's limits.

Run the mock grid, the record, and the paid steps in one clean checkout: the record
is committed on top of the commit it names, the mock grid stays where it ran, and a
later merge to ``main`` can't invalidate the record or a resume.

Usage (project lead, on the paid-run machine):
  python -m runner.spend_ledger init
  python -m runner.spend_ledger set-cap USD
  python -m runner.grid_dev mock
  python -m runner.paid_run record results/development/grid-mock --delivery PR --sandbox PR --request-to-effect PR
  git add protocol/paid_run_record.json && git commit
  python -m runner.paid_run check
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import marshal
import os
import platform
import re
import sqlite3
import struct
import subprocess
import sys
import tomllib
from datetime import date, datetime, timedelta, timezone
from importlib import metadata
from pathlib import Path, PurePosixPath
from typing import Any, Optional

from runner import spend_ledger
from runner.mock_provider import MOCK_MODEL_ID, MockProvider
from runner.mock_slice import EVENTS_FILE, REPO_ROOT, RESULTS_FILE, read_jsonl, validator
from tools import sandbox

RECORD = REPO_ROOT / "protocol" / "paid_run_record.json"
# Everything a paid grid cell executes or reads: code, the corpus and its fixtures,
# schemas, the grid spec, and the locked dependencies. Also the code that scores what
# it writes, whose checks and thresholds don't change after the first paid call
# (decision 0025 item 4).
HASHED_DIRS = (
    "agent", "analysis", "channels", "defenses", "oracles", "runner", "tasks", "tools",
    "corpus", "fixtures", "schemas", "paper/estimand_manifest.json", "protocol/development_grid_spec.json", "uv.lock",
)
RECORD_SCHEMA = "paid_run_record"
PROVENANCE_FILE = "code_provenance.jsonl"
# The Gate 2 scripts' own scoring code, which the digest in each invocation's provenance
# covers. analysis/price_bound.py stays out, so a raised bound can be re-evaluated.
SCORING_PATHS = (
    "analysis/__init__.py", "analysis/floor_count.py", "analysis/gate2_budget.py", "analysis/defense_readiness.py",
    "paper/estimand_manifest.json",
)
# A venv can hold these whatever uv.lock says, and uv sync doesn't remove them. Nothing a run
# imports comes from them, so they may be present unlocked, and what they are isn't pinned.
UNLOCKED_TOOLS = ("pip", "setuptools", "wheel")


# Decision 0026 item 3: a paid call asks the provider for one tool call per reply.
ONE_CALL_SETTINGS = (
    {"tool_choice": {"type": "auto", "disable_parallel_tool_use": True}},
    {"parallel_tool_calls": False},
)


class PaidRunRefused(ValueError):
    """A paid call was refused before it was made."""


def is_paid(provider: Any) -> bool:
    return provider is not None and not isinstance(provider, MockProvider)


def _git(*args: str, root: Path = REPO_ROOT) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True,
        env={"PATH": os.defpath, "LANG": "C.UTF-8"},
    ).stdout


def tracked_files(root: Path = REPO_ROOT) -> list[str]:
    return sorted(p for p in _git("ls-files", "-z", "--", *HASHED_DIRS, root=root).split("\0") if p)


def code_hashes(root: Path = REPO_ROOT) -> dict[str, str]:
    """SHA-256 of every git-tracked file under the hashed directories."""
    return {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in tracked_files(root)}


def _bytecode_differs(cached: Path, source: Path) -> bool:
    """Whether Python would run ``cached`` for ``source``, and it holds anything but what
    ``source`` compiles to. The checks up to the comparison are importlib's: a file failing
    them is recompiled, never run. Hash-based files are compared whatever their flags say,
    because Python can load one without reading the source, which no hash would see."""
    try:
        data = cached.read_bytes()
        stat = source.stat()
        if data[:4] != importlib.util.MAGIC_NUMBER or len(data) < 16:
            return False
        flags, first, second = struct.unpack("<III", data[4:16])
        if flags & ~0b11:
            return False
        if not flags & 0b01 and (first, second) != (int(stat.st_mtime) & 0xFFFFFFFF, stat.st_size & 0xFFFFFFFF):
            return False
        return marshal.loads(data[16:]) != compile(source.read_bytes(), str(source), "exec", dont_inherit=True)
    except (OSError, ValueError, EOFError, TypeError, SyntaxError):
        return True


def _is_harmless_ignored(root: Path, path: str) -> bool:
    """Whether an ignored ``path`` can't change a run: Finder's ``.DS_Store``, which can appear
    mid-grid, or ``__pycache__`` bytecode Python wouldn't load or that matches its source."""
    relative = PurePosixPath(path)
    if relative.name == ".DS_Store":
        return True
    if relative.parent.name != "__pycache__" or relative.suffix != ".pyc":
        return False
    source = relative.parent.parent / f"{relative.name.split('.')[0]}.py"
    if importlib.util.cache_from_source(str(source)) != path or not (root / source).is_file():
        return True  # another interpreter's or optimization level's, or its source is gone: never read
    return not _bytecode_differs(root / path, root / source)


def dirty_paths(root: Path = REPO_ROOT) -> list[str]:
    """Hashed paths that are uncommitted, untracked, or git-ignored. An ignored file is in
    no hash but can still change a run: a forged ``.pyc``, a leftover ``.sqlite``."""
    status = _git("status", "--porcelain", "-z", "--untracked-files=all", "--ignored", "--", *HASHED_DIRS, root=root)
    entries = iter(status.split("\0"))
    dirty = []
    for entry in entries:
        if not entry:
            continue
        code, path = entry[:2], entry[3:]
        if "R" in code or "C" in code:
            next(entries, None)  # -z gives a rename's old path its own field
        if code != "!!" or not _is_harmless_ignored(root, path):
            dirty.append(path)
    return dirty


def code_digest(hashes: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def scoring_digest(root: Optional[Path] = None) -> str:
    """The digest of the Gate 2 scripts' own scoring code, as it stands on disk."""
    root = root or REPO_ROOT
    return code_digest({path: hashlib.sha256((root / path).read_bytes()).hexdigest()
                        for path in SCORING_PATHS if (root / path).is_file()})


def python_environment() -> dict[str, Any]:
    """This interpreter's version and every installed distribution's."""
    packages: dict[str, str] = {}
    for distribution in metadata.distributions():
        name = re.sub(r"[-_.]+", "-", str(distribution.metadata["Name"])).lower()
        # Two copies of one package on the path can't both be the locked one.
        version = packages.get(name, distribution.version)
        packages[name] = version if version == distribution.version else f"{version}|{distribution.version}"
    return {"python": platform.python_version(), "packages": packages}


def lock_mismatch(environment: dict[str, Any], root: Path = REPO_ROOT) -> list[str]:
    """What's installed at a version ``uv.lock`` doesn't pin, Python included."""
    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    locked = {package["name"]: package.get("version") for package in lock["package"]}
    wrong = [f"{name} {version}" for name, version in sorted(environment["packages"].items())
             if locked.get(name) != version and (name in locked or name not in UNLOCKED_TOOLS)]
    series = re.fullmatch(r"==(\d+\.\d+)\.\*", lock["requires-python"])
    if series is None or not environment["python"].startswith(series[1] + "."):
        wrong.append(f"python {environment['python']}")
    return wrong


def _pinned(environment: dict[str, Any]) -> dict[str, Any]:
    """What the record and each invocation hold to: everything but the unlocked tools."""
    packages = {name: version for name, version in environment["packages"].items() if name not in UNLOCKED_TOOLS}
    return {**environment, "packages": packages}


def _lock_refusal(environment: dict[str, Any], root: Path) -> Optional[str]:
    try:
        wrong = lock_mismatch(environment, root)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return f"uv.lock can't say what should be installed: {exc}"
    return "installed packages don't match uv.lock: " + ", ".join(wrong[:5]) if wrong else None


def _machine_facts(root: Path) -> dict[str, Optional[str]]:
    """What a run ran on that no hash covers. Mock runs may have no sandbox or lock to name."""
    try:
        fingerprint = sandbox.describe()
    except sandbox.SandboxUnavailable:
        fingerprint = None
    lock = root / "uv.lock"
    return {"os_build": f"{platform.platform()} {platform.version()}", "python_build": sys.version,
            "sqlite_version": sqlite3.sqlite_version, "sandbox": fingerprint,
            "uv_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest() if lock.is_file() else None}


def code_provenance(root: Optional[Path] = None) -> dict[str, Any]:
    """The hashed code a run executes now: its commit, any uncommitted, untracked, or
    ignored hashed paths, and the digest of ``code_hashes``. Without git each is null,
    which ``build_record`` refuses. Also the digest of the scoring code, the digest of
    the environment it runs under, the cap, and the machine facts no hash covers."""
    root = root or REPO_ROOT
    facts = {"scoring_digest": scoring_digest(root), "environment": code_digest(_pinned(python_environment())),
             "spend_cap_usd": spend_ledger.cap_or_none(), **_machine_facts(root)}
    try:
        return {"code_commit": _git("rev-parse", "HEAD", root=root).strip(), "dirty_paths": dirty_paths(root),
                "code_digest": code_digest(code_hashes(root)), **facts}
    except (OSError, subprocess.CalledProcessError):
        return {"code_commit": None, "dirty_paths": None, "code_digest": None, **facts}


def _is_mock_run(run_dir: Path) -> bool:
    """Whether every result in ``run_dir`` says it ran on the mock. One that can't be read doesn't."""
    for results_path in Path(run_dir).glob(f"*/{RESULTS_FILE}"):
        try:
            for line in results_path.read_text(encoding="utf-8").splitlines():
                run_metadata = json.loads(line)["run_metadata"]
                if {run_metadata.get("model_requested"), run_metadata.get("model_resolved")} - {None} != {MOCK_MODEL_ID}:
                    return False
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return False
    return True


def check_code_matches_run(run_dir: Path, *, root: Optional[Path] = None) -> str:
    """The Gate 2 scripts' self-check, or ``PaidRunRefused``: their own scoring code must be
    what every invocation of ``run_dir`` recorded, so a threshold edited after the grid is
    refused. Only that is compared. A grid resumed across a fix to other hashed code stays
    scoreable, which matters because the ceiling rules out a second grid, and later report
    code elsewhere in ``analysis/`` doesn't refuse.

    The record plays no part, so the Gate 2 step's close (decision 0025 item 4; November 10 under decision 0029) evaluates whatever
    grid records exist, and a new record can't evade this. A mock run without provenance
    stays allowed, and the returned note, which goes in the report, says so; a non-mock run
    without it is refused, or deleting the file would evade the check.
    """
    root = root or REPO_ROOT
    try:
        text = (Path(run_dir) / PROVENANCE_FILE).read_text(encoding="utf-8")
    except FileNotFoundError:
        text = ""
    except OSError as exc:
        raise PaidRunRefused(f"{PROVENANCE_FILE} can't be read: {exc}") from exc
    try:
        # A line without its newline was cut off by a kill and never became durable.
        lines = [json.loads(line) for line in text.split("\n")[:-1] if line.strip()]
    except ValueError as exc:
        raise PaidRunRefused(f"{PROVENANCE_FILE} can't be read: {exc}") from exc
    if not all(isinstance(line, dict) for line in lines):
        raise PaidRunRefused(f"{PROVENANCE_FILE} holds a line that isn't a provenance record")
    if not lines:
        if not _is_mock_run(run_dir):
            raise PaidRunRefused(f"this non-mock run has no {PROVENANCE_FILE}, so nothing says what code ran it")
        return f"not compared: this mock run has no {PROVENANCE_FILE}, so nothing says this code ran it"
    forged = [path for path in SCORING_PATHS if path.endswith(".py") and (root / path).is_file()
              and (root / importlib.util.cache_from_source(path)).exists()
              and _bytecode_differs(root / importlib.util.cache_from_source(path), root / path)]
    if forged:
        raise PaidRunRefused("Python would load bytecode that differs from this source: " + ", ".join(forged))
    digest = scoring_digest(root)
    recorded = {line.get("scoring_digest") for line in lines}
    commits = ", ".join(sorted({str(line.get("code_commit")) for line in lines}))
    if len(recorded) > 1:
        raise PaidRunRefused(f"the invocations of {run_dir} ran different scoring code, so no checkout matches them all: "
                             f"commits {commits}")
    if recorded != {digest}:
        raise PaidRunRefused(f"this scoring code isn't what ran {run_dir}: run this script from commit {commits}")
    return f"compared: this scoring code ran the grid (scoring_digest {digest})"


def environment_refusal() -> Optional[str]:
    if "CI" in os.environ:
        return "CI is set; paid calls never run in CI"
    ambient = sorted(name for name in os.environ if name.startswith(("ANTHROPIC_", "OPENAI_")))
    if ambient:
        return "unset ambient provider variables first: " + ", ".join(ambient)
    return None


def load_record(path: Optional[Path] = None) -> dict[str, Any]:
    path = path or RECORD
    if not path.is_file():
        raise PaidRunRefused(f"no paid-run record at {path}; paid runs are closed until the project lead records one")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        validator(RECORD_SCHEMA).validate(record)
    except Exception as exc:
        raise PaidRunRefused(f"the paid-run record doesn't validate: {exc}") from exc
    return record


def _record_file_refusal(path: Path, root: Path) -> Optional[str]:
    """The record counts only as a committed file of this checkout, unchanged since."""
    try:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return f"the paid-run record must be a file in this checkout, not {path}"
    try:
        _git("ls-files", "--error-unmatch", "--", relative, root=root)
    except subprocess.CalledProcessError:
        return f"the paid-run record {relative} isn't committed; commit it first"
    if _git("status", "--porcelain", "--", relative, root=root).strip():
        return f"the paid-run record {relative} has uncommitted changes"
    return None


def _recorded_commit_refusal(record: dict[str, Any], root: Path) -> Optional[str]:
    """The recorded commit is on this history, and the record is dated from it to
    today. A day's slack either way covers the time zones of two machines."""
    commit = record["recorded_commit"]
    try:
        _git("merge-base", "--is-ancestor", commit, "HEAD", root=root)
        committed = datetime.fromtimestamp(int(_git("show", "-s", "--format=%ct", commit, root=root)), timezone.utc).date()
    except (subprocess.CalledProcessError, ValueError):
        return f"recorded_commit {commit} isn't an ancestor of HEAD"
    try:
        recorded_on = date.fromisoformat(record["recorded_on"])
    except ValueError:
        return f"recorded_on {record['recorded_on']} isn't a date"
    slack = timedelta(days=1)
    if not committed - slack <= recorded_on <= date.today() + slack:
        return f"recorded_on {recorded_on} isn't between recorded_commit's date {committed} and today"
    return None


def mock_run_digests(mock_run: Path) -> dict[str, str]:
    """What the record pins of its mock grid: the files that say how it ran, every
    result, and every event. ``OSError`` when the grid isn't there."""
    def digest(paths: list[Path]) -> str:
        hashed = hashlib.sha256()
        for path in sorted(paths):
            hashed.update(path.relative_to(mock_run).as_posix().encode("utf-8") + b"\0")
            hashed.update(hashlib.sha256(path.read_bytes()).digest())
        return hashed.hexdigest()

    from runner import execute

    run_files = [mock_run / name for name in (execute.SPEC_FILE, execute.MODE_FILE, PROVENANCE_FILE)]
    return {"run_files_sha256": digest(run_files), "results_sha256": digest(list(mock_run.glob(f"*/{RESULTS_FILE}"))),
            "events_sha256": digest(list(mock_run.glob(f"*/{EVENTS_FILE}")))}


def _mock_run_refusal(record: dict[str, Any], root: Path) -> Optional[str]:
    """The mock grid the record names is on disk, unchanged, and passes every check
    ``build_record`` makes. No digest in a file anyone can write proves a run
    happened, so the gate reads the run itself."""
    stated = record["conditions"]["mock_grid"]
    mock_run = root / stated["run_path"]
    if not mock_run.resolve().is_relative_to((root / "results").resolve()):
        return f"the mock grid {stated['run_path']} isn't under this checkout's results/"
    try:
        digests = mock_run_digests(mock_run)
    except OSError as exc:
        return f"the mock grid {stated['run_path']} isn't in this checkout: {exc}"
    if any(stated[field] != value for field, value in digests.items()):
        return f"the mock grid {stated['run_path']} changed after the record; record again"
    try:
        grid = _check_mock_run(mock_run, root=root)
    except PaidRunRefused as exc:
        return str(exc)
    for field in ("experiment_id", "tool_sandbox"):
        if grid[field] != stated[field]:
            return f"the record's mock grid {field} {stated[field]} isn't the run's {grid[field]}"
    if grid["tool_sandbox"] != record["sandbox"]:
        return f"the mock grid ran under {grid['tool_sandbox']!r}, not the record's {record['sandbox']!r}"
    return None


def paid_run_refusal(*, live_smoke: bool = False, record_path: Optional[Path] = None, root: Optional[Path] = None,
                     new_trials: int = 1) -> Optional[str]:
    """Why a paid call can't run now, or ``None`` when it may. ``new_trials`` is how many
    development trials this run still adds against SPEC.md Section 9's ceiling."""
    try:
        return _refusal(live_smoke, record_path, root or REPO_ROOT, new_trials)
    except (OSError, subprocess.CalledProcessError) as exc:
        return f"git can't say what this checkout holds: {exc}"


def _refusal(live_smoke: bool, record_path: Optional[Path], root: Path, new_trials: int) -> Optional[str]:
    reason = environment_refusal()
    if reason:
        return reason
    try:
        running = sandbox.describe()
    except sandbox.SandboxUnavailable as exc:
        return f"tool sandbox unavailable: {exc}"
    if live_smoke:
        # The one exception needs no record, but it still runs clean, locked code, and it spends.
        dirty = dirty_paths(root)
        if dirty:
            return "uncommitted or ignored changes in recorded code: " + ", ".join(dirty[:5])
        return _lock_refusal(python_environment(), root) or spend_ledger.refusal(new_trials=new_trials)
    try:
        record = load_record(record_path)
    except PaidRunRefused as exc:
        return str(exc)
    if record["sandbox"] != running:
        return f"this machine's tool sandbox {running!r} isn't the recorded mock grid's {record['sandbox']!r}"
    reason = _record_file_refusal(record_path or RECORD, root) or _recorded_commit_refusal(record, root)
    if reason:
        return reason
    dirty = dirty_paths(root)
    if dirty:
        return "uncommitted or ignored changes in recorded code: " + ", ".join(dirty[:5])
    current = code_hashes(root)
    if current != record["code_sha256"]:
        changed = sorted(p for p in set(current) | set(record["code_sha256"]) if current.get(p) != record["code_sha256"].get(p))
        return "code differs from the paid-run record: " + ", ".join(changed[:5])
    environment = python_environment()
    reason = _lock_refusal(environment, root)
    if reason:
        return reason
    if _pinned(environment) != _pinned(record["environment"]):
        return f"this environment isn't the record's (python {environment['python']}); record again under it"
    return _mock_run_refusal(record, root) or spend_ledger.refusal(new_trials=new_trials)


def require_paid_run(provider: Any, *, live_smoke: bool = False, record_path: Optional[Path] = None,
                     new_trials: int = 1) -> None:
    """Refuse a non-mock provider unless every paid-run condition holds."""
    if not is_paid(provider):
        return
    reason = paid_run_refusal(live_smoke=live_smoke, record_path=record_path, new_trials=new_trials)
    if reason:
        raise PaidRunRefused(reason)
    declared = json.dumps(getattr(provider, "request_settings", None), sort_keys=True)  # 0 isn't false
    if declared not in {json.dumps(settings, sort_keys=True) for settings in ONE_CALL_SETTINGS}:
        raise PaidRunRefused("the provider doesn't ask for one tool call per reply (decision 0026 item 3)")


def _mock_run_sandbox(run_dir: Path) -> str:
    modes = set()
    for events_path in run_dir.glob(f"*/{EVENTS_FILE}"):
        first = json.loads(events_path.read_text(encoding="utf-8").splitlines()[0])
        modes.add(first.get("component_versions", {}).get("tool_sandbox"))
    if len(modes) != 1 or None in modes:
        raise PaidRunRefused(f"the mock grid didn't run under one recorded tool sandbox: {sorted(map(str, modes))}")
    return modes.pop()


def _check_preflight(mock_run: Path, digest: str, corpus: Path) -> None:
    """Every invocation of the mock grid ran ``digest``'s code, clean, under this
    environment, with delivery, on ``corpus``."""
    from runner import execute

    try:
        mode = json.loads((mock_run / execute.MODE_FILE).read_text(encoding="utf-8"))
        text = (mock_run / PROVENANCE_FILE).read_text(encoding="utf-8")
        lines = [json.loads(line) for line in text.splitlines() if line.strip()]
    except (OSError, ValueError) as exc:
        raise PaidRunRefused(f"the mock grid didn't record the code it ran ({exc}); rerun it with this runner") from exc
    if mode != {"delivery": True}:
        raise PaidRunRefused("the mock grid didn't run with tool-result delivery")
    phases = [line.get("phase") for line in lines]
    if not phases or phases != ["start", "stop"] * (len(phases) // 2):
        raise PaidRunRefused("a mock grid invocation ended without recording its code; rerun the mock grid from the start")
    environment = code_digest(_pinned(python_environment()))
    for line in lines:
        dirty = line.get("dirty_paths")
        if dirty != []:
            raise PaidRunRefused("the mock grid ran with uncommitted changes in recorded code: "
                                 + (", ".join(dirty[:5]) if dirty else "unknown, without git"))
        if line.get("code_digest") != digest:
            raise PaidRunRefused(f"the mock grid ran other code (commit {line.get('code_commit')}) than this "
                                 "checkout; rerun it here")
        if line.get("corpus_root") != str(corpus):
            raise PaidRunRefused(f"the mock grid ran on {line.get('corpus_root')}, not this checkout's "
                                 "corpus/development")
        if line.get("environment") != environment:
            raise PaidRunRefused("the mock grid ran under other installed packages than this environment; rerun it here")


def _check_spec(mock_run: Path, spec: dict[str, Any]) -> None:
    """The grid ran the committed spec, on the mock (``grid_dev.run_mock_grid`` sets only the model)."""
    from runner import execute

    try:
        stored = json.loads((mock_run / execute.SPEC_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PaidRunRefused(f"the mock grid has no readable {execute.SPEC_FILE}: {exc}") from exc
    if stored != {**spec, "model_id": MOCK_MODEL_ID}:
        raise PaidRunRefused(f"the mock grid's {execute.SPEC_FILE} isn't the committed grid spec on the mock")


def _check_trials(mock_run: Path) -> None:
    """The task worked in every cell. A grid where nothing worked still verifies:
    ``verify_grid_run`` checks coverage and defense paths, not that a trial succeeded."""
    from runner import grid_dev

    problems: dict[str, list[str]] = {"didn't complete": [], "didn't end final_answer": [], "didn't pass utility": [],
                                      "hold a tool result that wasn't ok": []}
    conformance = []
    for results_path in sorted(mock_run.glob(f"*/{RESULTS_FILE}")):
        name = results_path.parent.name
        for record in read_jsonl(results_path, "result"):
            conformance.append(grid_dev.gate_conformance_refusal(record))
            if record["status"] != "completed":
                problems["didn't complete"].append(name)
            if record["termination_reason"] != "final_answer":
                problems["didn't end final_answer"].append(name)
            if record["utility"]["pass"] is not True:
                problems["didn't pass utility"].append(name)
        for event in read_jsonl(results_path.parent / EVENTS_FILE, "event"):
            if event["event_type"] == "tool_result" and event["payload"]["observation"].get("ok") is not True:
                problems["hold a tool result that wasn't ok"].append(name)
    for problem, names in problems.items():
        if names:
            raise PaidRunRefused(f"mock grid trials {problem}: " + ", ".join(sorted(set(names))[:5]))
    for reason in filter(None, conformance):
        raise PaidRunRefused(reason)


# Mock grids this process has read in full, so a paid grid reads its own once, not per trial.
_READ_MOCK_RUNS: dict[str, dict[str, Any]] = {}


def _check_mock_run(mock_run: Path, *, root: Path) -> dict[str, Any]:
    """Every fact the record rests on, read from the mock grid's own files, whether
    the record is being written or a paid run is about to rest on it. Returns what
    the record states about the grid."""
    from runner import grid_dev

    try:
        read_key = code_digest({"run": mock_run_digests(mock_run), "code": code_hashes(root), "root": str(root),
                                "environment": _pinned(python_environment())})
    except OSError:  # a file is missing: the checks below say which
        read_key = ""
    if read_key in _READ_MOCK_RUNS:
        return _READ_MOCK_RUNS[read_key]
    try:
        spec = grid_dev.load_spec(root / "protocol" / "development_grid_spec.json")
        # The named checks first, so a grid that fails one says which; then verify, which
        # also recomputes every stored result from its events and environment.
        _check_spec(mock_run, spec)
        _check_trials(mock_run)
        mode = _mock_run_sandbox(mock_run)
        _check_preflight(mock_run, code_digest(code_hashes(root)), (root / "corpus" / "development").resolve())
        summary = grid_dev.verify_grid_run(mock_run, spec)
        if not summary["complete"]:
            raise PaidRunRefused("the mock grid isn't complete")
    except PaidRunRefused:
        raise
    except Exception as exc:
        raise PaidRunRefused(f"the mock grid doesn't verify: {exc}") from exc
    grid = {"experiment_id": summary["experiment_id"], "trials": summary["trials_found"], "verify_complete": True,
            "tool_sandbox": mode}
    if read_key:
        _READ_MOCK_RUNS[read_key] = grid
    return grid


def build_record(mock_run: Path, *, delivery: str, sandbox_pr: str, request_to_effect: str,
                 recorded_by: str = "marek-sm", root: Optional[Path] = None) -> dict[str, Any]:
    root = root or REPO_ROOT
    mock_run = Path(mock_run).resolve()
    if not mock_run.is_relative_to((root / "results").resolve()):
        raise PaidRunRefused("run the mock grid under this checkout's results/, where every paid run can read it again")
    dirty = dirty_paths(root)
    if dirty:
        raise PaidRunRefused("commit or discard these changes before recording: " + ", ".join(dirty[:5]))
    environment = python_environment()
    reason = _lock_refusal(environment, root)
    if reason:
        raise PaidRunRefused(reason)
    grid = _check_mock_run(mock_run, root=root)
    mode = grid["tool_sandbox"]
    if mode != sandbox.describe():
        raise PaidRunRefused("record the paid run on the machine and sandbox the mock grid ran under")
    hashes = code_hashes(root)
    return {
        "schema_version": "1.1.0",
        "recorded_on": date.today().isoformat(),
        "recorded_by": recorded_by,
        "recorded_commit": _git("rev-parse", "HEAD", root=root).strip(),
        "sandbox": mode,
        "conditions": {
            "tool_result_delivery": {"merged_in": delivery},
            "mock_grid": {**grid, "run_path": mock_run.relative_to(root.resolve()).as_posix(), **mock_run_digests(mock_run)},
            "request_to_effect": {"merged_in": request_to_effect},
            "tool_sandbox": {"merged_in": sandbox_pr},
        },
        "code_sha256": hashes,
        "environment": environment,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("record", help="write protocol/paid_run_record.json from a verified mock grid")
    rec.add_argument("mock_run", type=Path)
    rec.add_argument("--delivery", required=True)
    rec.add_argument("--sandbox", required=True)
    rec.add_argument("--request-to-effect", required=True)
    sub.add_parser("check", help="say whether a paid run may start here")
    args = parser.parse_args(argv)
    if args.command == "record":
        try:
            record = build_record(args.mock_run, delivery=args.delivery, sandbox_pr=args.sandbox,
                                  request_to_effect=args.request_to_effect)
        except PaidRunRefused as exc:
            print(f"refusing: {exc}", file=sys.stderr)
            return 1
        validator(RECORD_SCHEMA).validate(record)
        RECORD.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {RECORD.relative_to(REPO_ROOT)}; commit it, then run paid steps from this checkout, "
              f"with the mock grid left at {record['conditions']['mock_grid']['run_path']}")
        return 0
    reason = paid_run_refusal()
    print(reason or "paid runs may start here")
    return 1 if reason else 0


if __name__ == "__main__":
    sys.exit(main())
