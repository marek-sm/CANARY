"""Development-floor count edges that mutation testing found unpinned
(reports/cloud/mutation.md). Each test names the surviving mutant it kills."""

import copy

import pytest

from analysis.floor_count import FLOOR_THRESHOLD, floor_count
from runner.mock_provider import MOCK_MODEL_ID
from tests.test_floor_count import BASES, CHANNELS, drop, events, grid, result


def test_missing_cells_are_charged_to_their_own_base():
    # Kills x_floor_count__mutmut_126 (by_base missing counted `c[0] != base`).
    # Two missing cells in one base: a symmetric drop across two bases can't tell.
    report = floor_count(drop(drop(grid(), "dev-001", "C2"), "dev-001", "C3"))
    assert report["by_base"]["dev-001"] == {"true": 0, "false": 1, "null": 0, "missing": 2}
    for base in BASES[1:]:
        assert report["by_base"][base] == {"true": 0, "false": 3, "null": 0, "missing": 0}
    assert report["by_adapter"]["C2"]["missing"] == 1
    assert report["by_adapter"]["C3"]["missing"] == 1
    assert report["by_adapter"]["C4"]["missing"] == 0


def test_the_report_names_its_cell_count_and_threshold():
    # Kills the key-renaming mutants on "cells" and "floor_threshold": Gate 3
    # copies these values with their source.
    report = floor_count(grid())
    assert report["cells"] == 15 == len(BASES) * len(CHANNELS)
    assert report["floor_threshold"] == FLOOR_THRESHOLD == 3
    assert report["experiment_id"] == "grid-dev"


@pytest.mark.parametrize("field", ["model_requested", "model_resolved"])
def test_a_mock_model_in_either_run_metadata_field_is_refused(field):
    # Kills x__is_mock__mutmut_5..10: only one of the two run-metadata fields names the mock.
    trials = grid()
    record, log = trials[0]
    record = copy.deepcopy(record)
    record["run_metadata"][field] = MOCK_MODEL_ID
    with pytest.raises(ValueError, match="mock"):
        floor_count([(record, log)] + trials[1:])


def test_a_mock_in_the_run_metadata_is_refused_even_when_every_attempt_names_a_live_model():
    # Kills x__is_mock__mutmut_16 (`models = ...` instead of `models |= ...`):
    # the attempts must add to the run metadata's models, never replace them.
    trials = grid()
    record, log = trials[0]
    record = copy.deepcopy(record)
    record["run_metadata"]["model_resolved"] = MOCK_MODEL_ID
    with pytest.raises(ValueError, match="mock"):
        floor_count([(record, log)] + trials[1:])


def test_a_mock_model_requested_in_an_attempt_alone_is_refused():
    # Kills x__is_mock__mutmut_18/21/22 (the attempt's model_requested key).
    trials = grid()
    record, log = trials[0]
    log = copy.deepcopy(log)
    log[1]["payload"]["model_requested"] = MOCK_MODEL_ID
    with pytest.raises(ValueError, match="mock"):
        floor_count([(record, log)] + trials[1:])


def test_a_non_d0_attack_record_from_a_mock_is_still_refused():
    # Mock refusal applies to every record in the run, not only the 15 floor cells.
    trials = grid()
    index = next(i for i, (r, _) in enumerate(trials) if r["configuration"] == "D2_DATAMARKING")
    record = result(trials[index][0]["base_case_id"], trials[index][0]["channel"], "clean", "D2_DATAMARKING",
                    model=MOCK_MODEL_ID)
    with pytest.raises(ValueError, match="mock"):
        floor_count(trials[:index] + [(record, events(record))] + trials[index + 1:])
