.PHONY: test trace paper-shells paper-shells-check
test:
	pytest -q

trace:
	python -m runner.mock_slice

paper-shells:
	python -m analysis.report_shells

paper-shells-check:
	python -m analysis.report_shells --check

.PHONY: t1-smoke
t1-smoke:
	python -m runner.ticket_slice

# Paid: one real call sequence on the decision 0010 development candidate (Anthropic).
# Run by hand only; refuses when CI or any ANTHROPIC_* or OPENAI_* variable is set.
.PHONY: live-smoke
live-smoke:
	python -m runner.live_smoke
