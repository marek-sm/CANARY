.PHONY: test trace paper-shells paper-shells-check
test:
	pytest -q

trace:
	python -m runner.mock_slice

paper-shells:
	python -m analysis.report_shells

paper-shells-check:
	python -m analysis.report_shells --check

.PHONY: t1-smoke t1-suite
t1-smoke:
	python -m runner.ticket_slice

# Offline tool/task acceptance only; each invocation gets a fresh output root.
t1-suite:
	python -m runner.task_suite --out $${TMPDIR:-/tmp}/canary-t1-suite-$$(date +%s)-$$$$

# Paid: one real OpenAI call sequence. Run by hand only; refuses when CI is set.
.PHONY: live-smoke
live-smoke:
	python -m runner.live_smoke
