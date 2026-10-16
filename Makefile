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
