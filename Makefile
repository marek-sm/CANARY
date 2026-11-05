.PHONY: test trace paper-shells paper-shells-check demo-example demo-example-check
# grid-check is part of test so CI needs no separate workflow edit (OAuth workflow scope).
test: grid-check
	pytest -q

trace:
	python -m runner.mock_slice

paper-shells:
	python -m analysis.report_shells

paper-shells-check:
	python -m analysis.report_shells --check

demo-example:
	python -m demo.accessibility

demo-example-check:
	python -m demo.accessibility --check

.PHONY: corpus-fixtures corpus-check
corpus-fixtures:
	python -m corpus.render_fixtures

corpus-check:
	python -m corpus.render_fixtures --check
	python -m corpus.intake

.PHONY: sandbox-check
# Decision 0023: every tool process runs sandboxed. Run once on a new machine; it
# fails if the sandbox can't confine a tool (macOS sandbox-exec, Linux bwrap).
sandbox-check:
	python -m pytest -q tests/test_tool_sandbox.py

.PHONY: t1-smoke t1-suite
t1-smoke:
	python -m runner.ticket_slice

t1-suite:
	python -m runner.task_suite --out "$$(mktemp -d)/task-suite"

# Paid: one real call sequence on the decision 0010 development candidate (Anthropic).
# Run by hand only; refuses when CI or any ANTHROPIC_* or OPENAI_* variable is set, and
# without python -m runner.spend_ledger init and set-cap, which the project lead runs once.
.PHONY: live-smoke
live-smoke:
	python -m runner.live_smoke

# Gate 2 step: the SPEC.md Section 10 development-floor count over the live
# development grid's run directory. Reads records only; makes no provider call.
.PHONY: floor-count
floor-count:
	python -m analysis.floor_count "$(RUN)" $(if $(OUT),--out "$(OUT)")

.PHONY: grid-validate grid-check grid-mock grid-verify grid-summary gate2-budget
grid-validate:
	python3 -m runner.grid_dev validate

# W7-T3: validate spec, grid tests, and the mock preflight through tool-result delivery (no paid calls).
grid-check: grid-validate
	pytest -q tests/test_grid_dev.py tests/test_grid_dev_full.py tests/test_grid_dev_live.py tests/test_grid_dev_defenses.py tests/test_gate2_budget.py
	@tmp=$$(mktemp -u -t canary-grid-mock-ci-XXXXXX); \
	trap 'rm -rf "$$tmp"' EXIT; \
	python3 -m runner.grid_dev mock --out "$$tmp" && python3 -m runner.grid_dev verify "$$tmp"

grid-mock:
	python3 -m runner.grid_dev mock $(if $(OUT),--out "$(OUT)") $(if $(filter true,$(RESUME)),--resume)

grid-verify:
	python3 -m runner.grid_dev verify "$(RUN)"

grid-summary:
	python3 -m runner.grid_dev summary "$(RUN)"

# Renders recorded traces: an events file, a trial, or every trial of a run (default:
# make grid-mock's output). Reads records only: no key, no provider, no network.
.PHONY: replay
replay:
	python3 -m demo.trace "$(or $(RUN),results/development/grid-mock)"

# The Gate 3 step runs this (TASKS.md). It generates what main has, the estimand shells,
# then runs W8-T3's analysis and report code, and fails in words until that code exists.
# REPORT_MODULE is a placeholder name: W8-T3 sets it to the module it commits.
REPORT_MODULE ?= analysis.report
.PHONY: report
report: paper-shells
	@python -c "import importlib.util, sys; sys.exit(importlib.util.find_spec('$(REPORT_MODULE)') is None)" || \
	  { echo "make report: $(REPORT_MODULE) isn't on this checkout. W8-T3 commits the analysis and report code; only the estimand shells (analysis.report_shells) were generated." >&2; exit 2; }
	python -m $(REPORT_MODULE)

gate2-budget:
	python3 -m analysis.gate2_budget "$(RUN)" --remaining-balance-usd "$(BALANCE)" $(if $(TIER),--tier "$(TIER)") $(if $(DEFENSE),--defense "$(DEFENSE)") $(if $(C1_PILOT),--c1-pilot-cost-usd "$(C1_PILOT)") $(if $(OUT),--out "$(OUT)")

# W7-T1: the mock checks are local and earn no development or live credit.
.PHONY: w7-t1-build w7-t1-check w7-t1-smoke w7-t1-evidence coverage-verify coverage-live raw-manifest
w7-t1-build:
	python -m runner.coverage --build
	python -m corpus.build_c1

w7-t1-check:
	python -m runner.coverage --check
	python -m corpus.build_c1 --check

w7-t1-smoke: w7-t1-check
	python -m runner.coverage --out "$$(mktemp -d)/coverage"
	python -m runner.c1_mock --out "$$(mktemp -d)/c1"

# Regenerates docs/evidence/w7-t1 from fresh mock runs of this checkout's code.
w7-t1-evidence: w7-t1-build
	@tmp=$$(mktemp -d); \
	trap 'rm -rf "$$tmp"' EXIT; \
	python -m runner.coverage --out "$$tmp/coverage" > /dev/null && \
	python -m runner.c1_mock --out "$$tmp/c1" > /dev/null && \
	cp "$$tmp/coverage/coverage-summary.json" "$$tmp/c1/c1-summary.json" docs/evidence/w7-t1/

# The smokes' 15-cell check (decision 0025 item 5). Reads records only; makes no provider call.
coverage-verify:
	python -m runner.coverage --verify "$(RUN)"

# Paid: the 15 clean smokes on a real provider, through the paid-run gate. Run by hand only (decision 0023 item 8).
coverage-live:
	python -m runner.coverage --live $(if $(OUT),--out "$(OUT)") $(if $(filter true,$(RESUME)),--resume)

# The SHA-256 manifest of raw results and events files (decision 0025 item 5): hashes only, safe to commit.
raw-manifest:
	python -m runner.raw_manifest $(RUNS) $(if $(OUT),--out "$(OUT)")
