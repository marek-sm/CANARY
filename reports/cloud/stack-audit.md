# CANARY stack audit: is each piece of the original stack doing its planned job?

Audited 2026-11-04 on `origin/main` `519e9af` (#70). `origin/cloud/integration` doesn't exist (`git ls-remote`), so there's nothing to compare. The baseline is the earliest `SPEC.md`, `README.md`, and `TASKS.md` (`149a706`) and the earliest `pyproject.toml`, `Dockerfile`, `compose.yaml`, `Makefile`, and `ci.yml` (`65288d3`). Each claim is tagged **ran** (I executed it here, as non-root user `auditor` with bwrap 0.9 and Docker 29.9.2) or **read** (from code or docs only).

## 1. Answer

No. Of 20 items, 8 are Adequate, 9 are Partly used, 1 is Nominal, and 2 are Unused (one of them, the sanitizer and release bundle, isn't built yet). The tools, the loop, the defenses, the evidence log, and the mock CI do their planned jobs on the path that produces records. Five things don't:

1. **Docker is Nominal.** The official sweep runs on the lead's Mac, outside the image. Every tool-launching command fails inside the image, and every record carries a null `container_digest`. Gate 3 still freezes a container digest, and `SPEC.md` §14's limitations don't mention any of this.
2. **The declared fallback can't run the grid.** `grid_dev live --provider openai --model gpt-6-luna` sends `claude-haiku-5-5` to OpenAI on all 90 trials, because the `--model` value is never used.
3. **Replay crashes on 54 of 90 mock-grid traces.** These are the same kind of records the sweep will produce.
4. **The pipeline from JSONL to results doesn't exist yet.** That covers analysis, `make report`, `make replay`, the sanitizer, `protocol/active.json`, and the manifest. Most of it is scheduled for W8-T3 by November 10, W9-T3 by November 12, and W12-T3.
5. **The pins bind files, not the running environment.** The paid-run gate accepts an installed environment that differs from `uv.lock`. `defense_hash` is null on every D1_POLICY_GATE and D2_DATAMARKING record.

## 2. Verdicts

| # | Item | Verdict | One-line reason |
|---|---|---|---|
| 1 | Python 3.11 | Adequate | Pinned in pyproject, CI, and the image (3.11.16), and the host venv (3.11.18). The Mac's version is unknown |
| 2 | Hand-written model/tool loop | Adequate | `agent/loop.py` drives every path. No agent framework is among the 28 locked packages |
| 3 | JSON Schema contracts | Partly used | Event, result, task, policy, and paid-run records are refused at runtime. Corpus schemas run in tests only, there's no schedule schema, and 3 planned schemas are absent |
| 4 | SQLite fixtures + authorizer | Adequate | A fixed registry and an in-memory copy. The authorizer denied all 10 write, ATTACH, extension, and schema attempts |
| 5 | Local HTTP fixture server | Partly used | Real HTTP on a Unix socket is on the delivery path, but it logs nothing, so "request logged" and the `fetch_url` effect oracle aren't backed |
| 6 | JSONL fake-sink receipts | Adequate | `send_email` appends a fsynced JSONL receipt, and delivery reads the sink for `sink_received` |
| 7 | Docker, pinned execution environment | **Nominal** | CI runs only the tool-free mock trace in it, tool paths fail in it, and the sweep runs outside it |
| 8 | Mock provider in CI | Adequate | CI runs only the mock provider. The paid paths refuse under `CI` |
| 9 | One adapter interface + fallback | **Partly used** | Two adapters exist, but the fallback can't be pointed at its model on the grid path and has no live evidence |
| 10 | D1_POLICY_GATE | Adequate | Wired into delivery dispatch, with golden vectors in tests. Its readiness check (#54) isn't merged |
| 11 | D2_DATAMARKING | Adequate | Wired into delivery: it marks resources and observations and adds its system instruction |
| 12 | Append-only JSONL evidence | Adequate | Records are fsynced and schema-validated on write and resume. `verify` refused tampered records |
| 13 | Analysis (estimands, bootstrap, tables) | Partly used | Only budget, floor, price, and request-effect scripts exist. No estimand or interval code |
| 14 | Replay | **Partly used** | The renderer works on the slice traces and crashes on 54/90 grid traces. There's no `make replay` |
| 15 | Demo + video | Partly used | A generated mock example exists. The demo case and video are later slices |
| 16 | Paper pipeline | Partly used | Only the estimand shells are generated. No tables or figures generator |
| 17 | `compose.yaml` | **Unused** | Nothing in the Makefile, CI, tests, or docs invokes it, and a tool run through it fails |
| 18 | `uv.lock` | Partly used | `--locked` in CI and the image, but the paid-run gate hashes the file, not the installed environment |
| 19 | Hash pins | **Partly used** | Fixture, corpus, prompt, policy, oracle, and code hashes are recorded. `defense_hash` and `container_digest` are null, and there's no `active.json` |
| 20 | Sanitizer + release bundle + manifest | Unused (not built) | Planned in `docs/DATA_RELEASE.md`. No code. W9-T3 and W11-T3 |

Added after the original plan: the tool sandbox (`tools/sandbox.py`, Linux `bwrap` plus the `no_exec.py` seccomp filter, macOS `sandbox-exec`; decision 0023), uv and `astral-sh/setup-uv`, the `anthropic` and `openai` SDKs, and the paid-run record (`protocol/paid_run_record.json`). On Linux the sandbox is Adequate: `make sandbox-check` passed 36 tests (**ran**). The macOS profile that the official sweep will use is never run in CI, which runs only `ubuntu-latest` (`.github/workflows/ci.yml:8,29`). It's verified only by the lead's report in decision 0023 (**read**).

## 3. Items that aren't Adequate, most serious first

### 3.1 Docker: Nominal
- **Plan:** "Docker for a pinned execution environment." (`149a706:SPEC.md:272`). Gate 3 freezes the "code commit and container digest" (`SPEC.md:1305`).
- **Today:** The image is digest-pinned and non-root (`Dockerfile:1,3,15-16`). CI builds it and runs only `runner.mock_slice`, which has no tools (`ci.yml:31-34`). Decisions 0023 and 0025 moved tool runs to the host and the sweep to the lead's Mac. `SPEC.md:304` now says "pinned CI environment", and the sweep "runs ... outside that container".
- **Ran:** The committed Dockerfile can't build here, because `ghcr.io/astral-sh/uv` blobs get a 403 from this session's egress proxy. That's an environment limit, not a repository defect. I built a variant whose only change is uv 0.12.18 taken from PyPI. `uv sync --locked` installed 21 packages, the container runs as uid 10001 on Python 3.11.16, and `docker run --network none --read-only ...` passed `make trace`. Inside the image, `runner.ticket_slice`, `runner.task_suite`, and `grid_dev mock` all fail with `SandboxUnavailable: bubblewrap (bwrap) is not installed`, and the image has no `make`.
- **Ran:** All 90 mock-grid records have `container_digest: null`. No code ever fills it: `runner/mock_slice.py:358` hard-codes `None`, and `runner/execute.py` doesn't set it.
- **Paths:** Unit tests and CI exercise only the trace. The mock grid, paid grid, official sweep, and replay never run in it. The release names "Docker instructions" (`SPEC.md:1493`).
- **Cost:** The environment the results come from isn't the pinned one. Anyone reproducing the sweep can't rebuild it from a digest. The Gate 3 container digest pins an image the sweep never ran in.
- **Fix:** Either run the sweep in an image that carries the sandbox, or record the host's environment (OS, Python, packages, sandbox profile hash) as the pin and stop calling the CI digest the Gate 3 container artifact. Gate 3 lists it, so the fix or a recorded reconciliation is needed by November 11.
- **Role change:** Decisions 0023 (item 9 and its Consequences) and 0025 (item 12). Item 12 says "Section 4, the manifest, and the paper state that limit". §4 does (`SPEC.md:304`). **§14's Mandatory limitations (`SPEC.md:1538-1552`) don't.**

### 3.2 Provider adapter interface and fallback: Partly used
- **Plan:** "One provider adapter interface so a fallback model can be selected **before** the full freeze" (`149a706:SPEC.md:274`).
- **Today:** `agent/anthropic_adapter.py` and `agent/openai_adapter.py` share `complete(...)`. In `runner/grid_dev.py:160`, `resolved_model = model or spec.get("model_id") or ...` is never used again. The schedule takes `spec["model_id"]`, and `runner/execute.py:747,823` sends `trial.model_id`.
- **Ran:** I replaced the client, key loader, and refusal check with stubs, with no network (`probes/fallback_probe.py`). `run_live_grid(provider_name="openai", model="gpt-6-luna")` builds an `OpenAIChatAdapter` over 90 trials, and every one requests `claude-haiku-5-5`.
- **Read:** `make live-smoke --provider openai` does honor `--model` (`runner/live_smoke.py:67`). STATUS says no OpenAI call has ever run. The fallback is unit-tested with a fake client only (`tests/test_openai_adapter.py`). No test runs the grid path with `openai`.
- **Cost:** If Haiku fails before the freeze, the declared fallback can't run the development grid without editing the hashed grid spec and writing a new paid-run record. A first attempt sends the wrong model ID and spends trials from the 120-trial ceiling.
- **Fix:** Put the model into the schedule, or commit a fallback grid spec, and add a test. It's a small change. It's needed before the November 11 freeze, because the fallback must be selectable before freeze (§9).

### 3.3 Replay: Partly used
- **Plan:** The `Append-only JSONL --> Analysis + replay + paper` edge (`149a706:SPEC.md:260-261`). "A one-keystroke completed-run replay ... starts in under ten seconds" (`:1408`). "Every replay is schema-valid" (`:1417`). `make replay` without a key (`:1266`).
- **Today:** `demo/trace.py` renders `events.jsonl`. `demo/trace.py:188` assumes every tool observation has a `text` field, but `query_db` returns `rows`.
- **Ran:** `python -m demo.trace` over my 90 mock-grid traces: 36 rendered and 54 failed with `KeyError: 'text'` (all 30 C2, 12 C3, 12 C4). It works on `make trace` and `t1-smoke`. There's no `make replay` target.
- **Cost:** The demo's fallback, the release replay, and Gate 5 all depend on replaying sweep records, and today most of those records can't be replayed.
- **Fix:** Make the renderer handle `rows` and the other observation shapes, and add a known-trace test on delivery records. W7-T5 (#66, unmerged, not checked here) and W11-T5 own replay. W12-T3 proves `make replay` (November 30–December 2). Gate 3 doesn't need it.

### 3.4 Analysis, report, and paper pipeline: Partly used
- **Plan:** "Analysis + replay + paper" (`149a706:SPEC.md:261`), 10,000 cluster-bootstrap draws (`:1166`), and `make report` (`:1266`).
- **Today:** `analysis/` holds `floor_count`, `gate2_budget`, `price_bound`, `request_effect`, and `report_shells`. Nothing computes the estimands, macro-averages, missingness ranges, or bootstrap. `make report` doesn't exist, yet the Gate 3 step runs it (`TASKS.md:95`).
- **Ran:** `make paper-shells-check` and `make demo-example-check` (see §4).
- **Cost:** Until it exists, no result can be generated, and the "analysis freezes before outcomes" rule (§10) can't be met.
- **Fix:** W8-T3 (Samson, merged by November 10) commits the "analysis and report code plus empty generated outputs". W8-T5 (Miles, PR due November 5) freezes the output pipeline. No slice names adding the `make report` target. It must exist by Gate 3.

### 3.5 Hash pins: Partly used
- **Plan:** "fixed prompt template and fixture hash" (`149a706:SPEC.md:302`). "record every applicable version/hash before the first provider call" (`:934`). The `defense_hash` field (`:772`).
- **Ran:** The grid records carry `code_commit`, `corpus_hash`, `prompt_hash`, `rendered_fixture_hash`, `task_policy_hash`, and `utility_oracle_hash`. **`defense_hash` is null on all 90, including all 60 D1/D2 trials.** Nothing in `runner/execute.py` sets it. The defense versions appear only as strings in `component_versions` (`runner/delivery.py:209-212`).
- **Read:** The Dockerfile digests and the `setup-uv` SHA are pinned. `actions/checkout@v4` is a tag (`ci.yml:12,30`). `protocol/active.json` is absent; W8-T3's generator is due by November 10.
- **Fix:** Hash the frozen gate and transform, write the hash into `defense_hash`, and pin `checkout` by SHA. Before Gate 3, because W8-T4 freezes and hashes the defenses then.

### 3.6 `uv.lock`: Partly used
- **Plan:** "`uv.lock` # frozen Python dependency resolution" (`149a706:SPEC.md:1626`). The first `pyproject.toml` and `Dockerfile` (`65288d3`) used bare `pip install` with no lock.
- **Ran:** `uv sync --locked` succeeds. I wrote a paid-run record in my scratch clone (deleted afterward), then installed `jsonschema` 4.21.1 into `.venv` while the lock says 4.26.0. `uv run --no-sync python -m runner.paid_run check` printed "paid runs may start here". The gate hashes `uv.lock` (`runner/paid_run.py:55`), not the installed environment. Plain `uv run` would re-sync, but the Make targets call bare `python`.
- **Side finding (ran):** The same record refuses when invoked as `.venv/bin/python` instead of `uv run python`, because the sandbox fingerprint changes. It fails closed, but it's fragile.
- **Fix:** Record and check the installed distributions against the lock, or require `uv run --locked`. Before the sweep starts on November 11.

### 3.7 JSON Schema contracts: Partly used
- **Plan:** "JSON Schema for corpus, schedule, event, and result contracts" (`149a706:SPEC.md:270`). `149a706:docs/DATA_CONTRACTS.md:9-15` also planned `engineering_validation`, `active_protocol`, and `manifest` schemas.
- **Ran:** In copies of the mock grid, a result with `model_requested: 12345` and an event with an unknown `event_type` were refused by `grid_dev verify` (exit 1), and the bad event was also refused on `--resume` (exit 1). Every schema rejects `{}`.
- **Ran:** A `dev-001` base case with no `source` fails `base_case.schema.json`, but `runner/execute.py:322` `_load_base` accepts it. The corpus schemas are enforced only by `tests/test_corpus_records.py`.
- **Read:** The schedule comes from `protocol/development_grid_spec.json`, which Python code checks; there's no schedule schema. The `engineering_validation`, `active_protocol`, and `manifest` schemas don't exist. W8-T3 owns the validation schema and the `active.json` generator. No slice names the `active_protocol` or `manifest` schema.
- **Fix:** Validate base cases when they're loaded, and add the missing schemas. The `active_protocol` schema is needed before Gate 3.

### 3.8 Local HTTP fixture server: Partly used
- **Plan:** `fetch_url` "Exact local-origin allowlist; redirects off; request logged" (`149a706:SPEC.md:284`). The effect counts when "a local request completes and the fixture server logs it" (`:554`).
- **Ran:** Through the sandboxed worker, an allowlisted URL returned exactly the page from `pages.json`. An off-list URL got `url_outside_fixture_allowlist`. With no endpoint, it got `fixture_service_unavailable`. With the server stopped, the worker launch failed (bwrap exit 1). The delivery path starts this server (`runner/execute.py:806`).
- **Read:** `tools/fixture_http.py:113-114` makes `log_message` a no-op, and nothing else records requests. The effect oracle is `fetch_url-returned-v0.1.0`, which copies the tool's own `ok` (`runner/delivery.py:103,568-573`). `SPEC.md:316,590` still promise a server log.
- **Cost:** `effect_observed` for `fetch_url` isn't independent evidence. It repeats the tool's return value.
- **Fix:** Have the server append each request to a per-trial JSONL log in its writable directory, and score from that. Before Gate 3, because the effect oracle freezes with W8-T1. The move from loopback TCP to a Unix socket is decision 0023 item 2. It doesn't weaken the plan, and §14 doesn't need it.

### 3.9 `compose.yaml`: Unused
- **Plan:** It's in the layout (`149a706:SPEC.md:1624`). `65288d3:compose.yaml` defines a `mock` service with `network_mode: none`.
- **Ran:** `docker compose run mock` (variant image) prints the mock trace. `docker compose run mock python -m runner.ticket_slice` exits 1 with `SandboxUnavailable`. `grep` finds no use in the Makefile, CI, tests, or docs, except decision 0023:93: "`compose.yaml` (audit F-07) stays a separate item". It has no owner and no date.
- **Fix:** Wire it into a documented command with the CI job's flags, or decide its role in a record. Not needed by Gate 3.

### 3.10 Smaller Partly-used items
- **Demo (read):** `demo/accessibility.py` makes a labeled mock example. The demo case, the stage run, and the video are W7-T5 (#66), W11-T5, and W12-T1.
- **Sanitizer, release bundle, manifest (read):** Nothing implements them. `results/public/` and `results/development/` are empty. W9-T3 (PR due November 12) builds the sanitizer, and W11-T3 freezes the manifests. `LICENSE` and `CITATION.cff` are absent, owned by W11-T5.

### 3.11 Planned but not implemented (read)
- **Scheduled in `TASKS.md`:** `protocol/active.json`, its generator, the analysis and report code, the dormant `ENGINEERING` plan and validation schema (W8-T3, Samson, merged by November 10). The output pipeline (W8-T5, Miles, PR due November 5). An official-sweep entry point: `grid_dev live` refuses every corpus except `corpus/development` (`runner/grid_dev.py:130-131`), and the sweep is W9-T3, November 11–14. The sanitizer (W9-T3, PR due November 12). Manifests (W11-T3). `LICENSE` and `CITATION.cff` (W11-T5). Fresh-clone `make report` and `make replay` proven (W12-T3, November 30–December 2). The video (W12-T1).
- **No owner:** adding the `make report` and `make replay` targets, though the Gate 3 step runs `make report` (`TASKS.md:95`); `compose.yaml` (F-07); a schedule JSON Schema; the `active_protocol` and `manifest` schemas; a fixture-server request log; filling `defense_hash` and `container_digest`; fixing fallback model selection; replay for `rows` observations; checking the installed environment against `uv.lock`.

### 3.12 Stack claims the code doesn't back
- `SPEC.md:316` says the `fetch_url` request is logged, and `SPEC.md:590` says the effect counts when "the fixture server logs it". The server logs nothing (§3.8).
- `SPEC.md:1305` freezes the "container digest" at Gate 3, but the sweep never runs in that container (§3.1).
- `SPEC.md:304` and decision 0025 item 12 say "the manifest and paper state that limit". Neither exists yet, and §14 omits it.
- §9 asks for "every applicable version/hash" before the first call, and §8 has `defense_hash`, but it's null on D1/D2 (§3.5).
- `SPEC.md:1493` lists "Docker instructions" in the public repository, and `README.md` has none.
- §9 and decision 0010 item 3 say the fallback can be selected through `agent/openai_adapter.py`. The grid path can't target it (§3.2).
- README claims I checked and found backed: `t1-smoke` runs through "replay" (`README.md:131-133`, **ran**), and the "private page service on a per-trial Unix socket" with every tool sandboxed (`README.md:141-142`, **ran** on Linux).

## 4. Commands run, with raw counts

All of these ran as `auditor` in `~/work/CANARY` at `519e9af`, after `uv sync --locked`, on the 4-CPU VM unless noted.

| Command | Result |
|---|---|
| `uv run make sandbox-check` | 36 passed in 6.12 s |
| `uv run make test` | grid-validate 90 trials; grid tests 61 passed (185 s); `pytest -q` 1907 passed (263 s); 0 failed; total 7 m 55 s |
| `uv run make trace` | exit 0, 51 lines, mock trace rendered |
| `uv run make t1-smoke` / `t1-suite` | exit 0 (ticket replay rendered) / exit 0, 20 of 20 variants `utility=True` |
| `uv run make grid-check` | PENDING. Inside `make test`: `grid_dev validate` printed "90 trials", and the mock verify printed `complete: true, 90/90` |
| `uv run make w7-t1-smoke`, `corpus-check`, `paper-shells-check`, `demo-example-check` | PENDING |
| `uv run make report` / `make replay` | PENDING (no such targets in `Makefile`) |
| `python -m runner.grid_dev mock --out ~/gridrun` then `verify` | 90/90 complete, 22.8 s, verify exit 0 |
| `python -m demo.trace` on each of the 90 traces | 36 ok, 54 `KeyError: 'text'` |
| Tampered result and event, then `grid_dev verify` / `mock --resume` | exit 1, exit 1, exit 1 |
| `docker build` (committed Dockerfile) | Failed: 403 on `pkg-containers.githubusercontent.com` (proxy policy) |
| `docker build` (variant, uv from PyPI) and the CI `docker run` flags | Built. Trace exit 0, 46 lines |
| The same image: `ticket_slice`, `task_suite`, `grid_dev mock`; `docker compose run mock ...` | All `SandboxUnavailable`; compose exit 1 |
| SQLite authorizer probe (10 statements) | 10/10 denied |
| Fallback probe | 90 trials, model `claude-haiku-5-5`, adapter `OpenAIChatAdapter` |
| `paid_run check` with `jsonschema` 4.21.1 against lock 4.26.0 | "paid runs may start here" |

## 5. What I didn't check

- I made no real provider call and used no key, so the paid grid and the live smoke weren't run. Those paths are **read** only.
- The macOS `sandbox-exec` path, the lead's Mac, and its Python version are unknown.
- I didn't build the committed Dockerfile byte for byte. Its uv layer was unreachable from this VM.
- I didn't read the unmerged PRs #54, #66, or #73, or any other branch, and I didn't read `corpus/evaluation/`. I did run one `ls corpus/evaluation` by mistake while setting up. It printed nothing, and I read no file there.
- I didn't check the CI run history on GitHub.
- For about 20 seconds I changed `jsonschema` in the shared `.venv` while `make test` was running, then restored it with `uv sync --locked`.
