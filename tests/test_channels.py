import hashlib
import json
from pathlib import Path

from channels.render import (
    INSERTION_MARKER,
    parse_c2,
    parse_c3,
    parse_c4,
    render_c2,
    render_c3,
    render_c4,
    substitute,
)

FIXTURE_DIR = Path("fixtures/dev-001")
CANDIDATE_PATH = Path("corpus/development/dev-001.json")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_base_case():
    return json.loads(CANDIDATE_PATH.read_text())


def _template() -> str:
    return FIXTURE_DIR.joinpath("content.template.txt").read_text().rstrip("\n")


def _attack_and_clean_content(base_case):
    template = _template()
    payload = base_case["attack"]["canonical_payload"]
    clean = base_case["fixture"]["clean_replacement"]
    return substitute(template, payload), substitute(template, clean)


def test_template_has_exactly_one_insertion_marker():
    template = _template()
    assert template.count(INSERTION_MARKER) == 1


def test_base_case_hashes_match_recorded_values():
    base_case = _load_base_case()
    template = _template()
    assert _sha256(template) == base_case["fixture"]["template_sha256"]
    assert (
        _sha256(base_case["attack"]["canonical_payload"])
        == base_case["attack"]["canonical_payload_sha256"]
    )
    assert (
        _sha256(base_case["fixture"]["clean_replacement"])
        == base_case["fixture"]["clean_replacement_sha256"]
    )


def test_structural_diff_attack_and_clean_differ_only_at_slot():
    base_case = _load_base_case()
    template = _template()
    prefix, suffix = template.split(INSERTION_MARKER)
    attack_content, clean_content = _attack_and_clean_content(base_case)

    assert attack_content.startswith(prefix)
    assert attack_content.endswith(suffix)
    assert clean_content.startswith(prefix)
    assert clean_content.endswith(suffix)

    attack_slot = attack_content[len(prefix) : len(attack_content) - len(suffix)]
    clean_slot = clean_content[len(prefix) : len(clean_content) - len(suffix)]
    assert attack_slot == base_case["attack"]["canonical_payload"]
    assert clean_slot == base_case["fixture"]["clean_replacement"]
    assert attack_slot != clean_slot


CHANNEL_RENDERERS = {
    "C2": (render_c2, parse_c2),
    "C3": (render_c3, parse_c3),
    "C4": (render_c4, parse_c4),
}


def test_every_channel_round_trips_attack_and_clean_content():
    base_case = _load_base_case()
    attack_content, clean_content = _attack_and_clean_content(base_case)

    for channel, (render, parse) in CHANNEL_RENDERERS.items():
        for content in (attack_content, clean_content):
            rendered = render(content)
            recovered = parse(rendered)
            assert recovered == content, f"{channel} round-trip mismatch"


def test_rendered_fixtures_on_disk_match_hash_manifest():
    manifest = json.loads(FIXTURE_DIR.joinpath("rendered-hashes.json").read_text())
    for key in ("c2_attack", "c2_clean", "c3_attack", "c3_clean", "c4_attack", "c4_clean"):
        entry = manifest[key]
        rendered = Path(entry["path"]).read_text()
        assert _sha256(rendered) == entry["sha256"], f"{key} hash drifted from disk"


def test_rendered_bytes_differ_by_channel_but_recover_the_same_canonical_payload():
    base_case = _load_base_case()
    attack_content, _ = _attack_and_clean_content(base_case)

    rendered_by_channel = {
        channel: render(attack_content) for channel, (render, _) in CHANNEL_RENDERERS.items()
    }
    # Serialization differs across channels (JSON vs. plain text vs. HTML)...
    assert len({rendered_by_channel["C2"], rendered_by_channel["C3"], rendered_by_channel["C4"]}) == 3

    # ...but every channel parser recovers the identical canonical payload.
    for channel, (_, parse) in CHANNEL_RENDERERS.items():
        assert parse(rendered_by_channel[channel]) == base_case["attack"]["canonical_payload"]
