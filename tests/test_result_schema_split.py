"""Blocker 2: the result schema now carries a required ``split`` and, for the
evaluation split, requires non-null protocol_version/channel/condition/
comparison_superblock_id. Development trials may leave those null."""
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from runner.mock_slice import validator

FIXTURES = Path(__file__).parent / "fixtures" / "result"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_development_result_validates():
    # development may leave protocol_version/channel/condition/superblock null
    result = load("valid_development.json")
    assert result["split"] == "development"
    assert result["channel"] is None and result["protocol_version"] is None
    validator("result").validate(result)


def test_valid_evaluation_result_validates():
    result = load("valid_evaluation.json")
    assert result["split"] == "evaluation"
    for field in ("protocol_version", "channel", "condition", "comparison_superblock_id"):
        assert result[field] is not None, field
    validator("result").validate(result)


def test_invalid_evaluation_missing_required_nonnull_field_rejected():
    # evaluation split with a null channel must fail (then-branch removes null)
    result = load("invalid_evaluation_null_channel.json")
    assert result["split"] == "evaluation" and result["channel"] is None
    with pytest.raises(ValidationError):
        validator("result").validate(result)


def test_invalid_split_value_rejected():
    result = load("invalid_bad_split.json")
    assert result["split"] == "production"
    with pytest.raises(ValidationError):
        validator("result").validate(result)


def test_split_is_required():
    result = load("valid_development.json")
    del result["split"]
    with pytest.raises(ValidationError):
        validator("result").validate(result)


def test_development_split_permits_nonnull_identifiers_too():
    # development is permissive: non-null channel/condition are also valid
    result = load("valid_development.json")
    result["channel"] = "C2"
    result["condition"] = "attack"
    validator("result").validate(result)
