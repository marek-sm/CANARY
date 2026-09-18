.PHONY: test trace
test:
	pytest -q

trace:
	python -m runner.mock_slice
