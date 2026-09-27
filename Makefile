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
