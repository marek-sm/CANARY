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

.PHONY: corpus-fixtures corpus-check
corpus-fixtures:
	python -m corpus.render_fixtures

corpus-check:
	python -m corpus.render_fixtures --check
	python -m corpus.intake

.PHONY: t1-smoke t1-suite
t1-smoke:
	python -m runner.ticket_slice

t1-suite:
	python -m runner.task_suite --out "$$(mktemp -d)/task-suite"

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

# Gate 2 step: the binary D1_POLICY_GATE and D2_DATAMARKING readiness checks
# (SPEC.md Section 12, rule 3) over the same run directory. Reads records and
# runs the committed defense tests; makes no provider call. CONTEXT and RESERVE
# are the model's context window and the output/tool-loop reserve, in tokens.
.PHONY: defense-readiness
defense-readiness:
	python -m analysis.defense_readiness "$(RUN)" --context-window "$(CONTEXT)" --output-reserve "$(RESERVE)" $(if $(OUT),--out "$(OUT)")
