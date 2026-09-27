import json
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENT = ROOT / "corpus" / "development" / "task-assignment.json"

# SPEC.md Section 4: the ten quantitative task templates.
SPEC_TEMPLATE_COUNTS = {
    "read_query": 3,
    "local_web_extraction": 2,
    "cross_source_comparison": 1,
    "legitimate_high_risk": 4,
}
CHANNEL_TOOLS = {"C2": "query_db", "C3": "read_file", "C4": "fetch_url"}


def assignment():
    return json.loads(ASSIGNMENT.read_text(encoding="utf-8"))


def test_five_development_bases_each_get_a_distinct_template():
    bases = assignment()["bases"]
    assert [b["base_case_id"] for b in bases] == [f"dev-00{i}" for i in range(1, 6)]
    assert len({b["template_id"] for b in bases}) == 5


def test_assigned_and_remaining_templates_add_up_to_the_spec_ten():
    doc = assignment()
    assert doc["template_counts"] == SPEC_TEMPLATE_COUNTS
    assigned = Counter(b["category"] for b in doc["bases"])
    remaining = doc["remaining_templates"]["counts"]
    for category, total in SPEC_TEMPLATE_COUNTS.items():
        assert assigned[category] + remaining[category] == total, category


def test_every_channel_names_its_tool_and_a_local_resource():
    for base in assignment()["bases"]:
        assert set(base["channels"]) == set(CHANNEL_TOOLS), base["base_case_id"]
        for channel, spec in base["channels"].items():
            assert spec["tool"] == CHANNEL_TOOLS[channel]
            resource = spec["resource"]
            if channel == "C3":
                path = PurePosixPath(resource)
                assert not path.is_absolute() and ".." not in path.parts, resource
            if channel == "C4":
                url = urlsplit(resource)
                assert url.scheme == "http" and url.hostname.endswith(".fixture.test"), resource


def test_high_risk_bases_name_a_fixture_recipient():
    for base in assignment()["bases"]:
        if base["category"] == "legitimate_high_risk":
            assert base["preauthorized_recipient"].endswith("@fixture.test")


def test_dev_001_matches_its_committed_record():
    record = json.loads((ROOT / "corpus" / "development" / "dev-001.json").read_text(encoding="utf-8"))
    dev_001 = assignment()["bases"][0]
    for channel, spec in dev_001["channels"].items():
        assert record["channels"][channel]["tool"] == spec["tool"]
        assert record["channels"][channel]["resource"] == spec["resource"]
