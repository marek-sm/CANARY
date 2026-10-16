.PHONY: test trace paper-shells paper-shells-check demo-example demo-example-check
test:
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

.PHONY: t1-smoke
t1-smoke:
	python -m runner.ticket_slice

# Paid: one real call sequence on the decision 0010 development candidate (Anthropic).
# Run by hand only; refuses when CI or any ANTHROPIC_* or OPENAI_* variable is set.
.PHONY: live-smoke
live-smoke:
	python -m runner.live_smoke

# Gate 2 step: the SPEC.md Section 10 development-floor count over the live
# development grid's run directory. Reads records only; makes no provider call.
.PHONY: floor-count
floor-count:
	python -m analysis.floor_count "$(RUN)" $(if $(OUT),--out "$(OUT)")

.PHONY: grid-validate grid-check grid-mock grid-verify gate2-budget
grid-validate:
	python3 -m runner.grid_dev validate

# W7-T3: validate spec, grid tests, and mock preflight on fixture corpus (no paid calls).
grid-check: grid-validate
	pytest -q tests/test_grid_dev.py tests/test_grid_dev_full.py tests/test_grid_dev_live.py tests/test_gate2_budget.py
	@tmp=$$(mktemp -u -t canary-grid-mock-ci-XXXXXX); \
	trap 'rm -rf "$$tmp"' EXIT; \
	python3 -m runner.grid_dev mock --corpus-root tests/fixtures/corpus/development --out "$$tmp"

grid-mock:
	python3 -m runner.grid_dev mock $(if $(OUT),--out "$(OUT)") $(if $(filter true,$(RESUME)),--resume)

# W7-T3 mock preflight using test fixture corpus (until W6-T2 #34 is on main).
.PHONY: grid-mock-fixtures
grid-mock-fixtures:
	@out="$(if $(OUT),$(OUT),$$(mktemp -u -t canary-grid-mock-XXXXXX))"; \
	if [ -e "$$out" ]; then \
	  echo "refusing: $$out already exists; remove it or set OUT= to a new directory" >&2; exit 1; fi; \
	python3 -m runner.grid_dev mock --corpus-root tests/fixtures/corpus/development --out "$$out"; \
	echo "grid mock run directory: $$out"

grid-verify:
	python3 -m runner.grid_dev verify "$(RUN)"

gate2-budget:
	python3 -m analysis.gate2_budget "$(RUN)" --remaining-balance-usd "$(BALANCE)" --conservative-c1-trial-cost-usd "$(C1_COST)" $(if $(RESERVE),--reserve-usd "$(RESERVE)",) $(if $(OUT),--out "$(OUT)")
