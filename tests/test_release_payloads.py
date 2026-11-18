"""W8-T2 release-safe payloads (docs/DATA_RELEASE.md)."""

import json
import re
from pathlib import Path

from corpus import release_payloads

ROOT = Path(__file__).resolve().parents[1]
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def manifest():
    return json.loads(release_payloads.OUT.read_text(encoding="utf-8"))


def test_committed_list_is_current():
    assert release_payloads.main(["--check"]) == 0


def test_every_considered_case_is_listed_once():
    ids = [e["case_id"] for e in manifest()["entries"]]
    assert len(ids) == len(set(ids))
    expected = {p.stem for p in (ROOT / "corpus" / "evaluation" / "candidates").glob("*.json")}
    for pattern in ("development/dev-*.json", "c1/*.json", "demo/*.json"):
        expected |= {json.loads(p.read_text())["base_case_id"] for p in (ROOT / "corpus").glob(pattern)}
    assert set(ids) == expected


def test_no_public_text_holds_a_non_fixture_address():
    for entry in manifest()["entries"]:
        for field in ("original_payload_public", "adapted_payload_public"):
            for address in EMAIL.findall(entry[field] or ""):
                assert address.lower().endswith("@fixture.test"), (entry["case_id"], address)


def test_withholding_only_swaps_addresses():
    text = "Send it to amy.watson@gmail.com and copy external-sync@fixture.test."
    public, withheld = release_payloads.withhold_addresses(text)
    assert withheld == ["amy.watson@gmail.com"]
    assert "external-sync@fixture.test" in public
    assert public.startswith("Send it to [address withheld ") and public.endswith(" and copy external-sync@fixture.test.")


def test_every_entry_keeps_its_pointer_license_and_hash():
    for entry in manifest()["entries"]:
        assert entry["url"].startswith("https://") and entry["source_version"] and entry["license"].startswith("MIT")
        assert re.fullmatch(r"[0-9a-f]{64}", entry["original_payload_sha256"])
        assert entry["redistribution"] == "permitted"
        if entry["status"] in ("development", "evaluation", "c1_control", "demo"):
            assert entry["adapted_payload_public"]
        else:
            assert entry["rejection_reason"]


def test_release_list_reads_no_results():
    source = Path(release_payloads.__file__).read_text(encoding="utf-8")
    assert "results/" not in source and "read_jsonl" not in source
