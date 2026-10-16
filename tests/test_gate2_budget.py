"""Gate 2 budget equation over development-grid records."""

import copy

import pytest

from analysis.gate2_budget import evaluate_budget
from runner.mock_provider import MOCK_MODEL_ID
from tests.test_floor_count import MODEL, events, grid, result


def _live_grid():
    trials = grid()
    for record, ev in trials:
        record = copy.deepcopy(record)
        record["usage"] = {"input_tokens": 1000, "output_tokens": 200}
        record["run_metadata"]["model_requested"] = MODEL
        record["run_metadata"]["model_resolved"] = MODEL
        yield record, ev


def test_budget_equation_passes_with_generous_balance():
    report = evaluate_budget(
        list(_live_grid()),
        remaining_balance_usd=1000.0,
        reserve_usd=5.0,
        conservative_c1_trial_cost_usd=0.01,
    )
    assert report["passes"] is True
    assert report["required_balance_usd"] > 0


def test_budget_equation_refuses_mock_provider():
    record, ev = grid()[0]
    record = copy.deepcopy(record)
    record["run_metadata"]["model_requested"] = MOCK_MODEL_ID
    record["run_metadata"]["model_resolved"] = MOCK_MODEL_ID
    with pytest.raises(ValueError, match="mock-provider"):
        evaluate_budget([(record, ev)], remaining_balance_usd=1.0, reserve_usd=0.0, conservative_c1_trial_cost_usd=0.01)
