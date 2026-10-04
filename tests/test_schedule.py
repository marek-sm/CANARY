"""Tests for the pure, data-driven schedule generator (W6-T3 A1/A6)."""

import pytest

from runner import schedule as sched


def _spec(**overrides):
    base = {
        "experiment_id": "exp-fixed",
        "model_id": "mock-canned-v0",
        "seed": "sd",
        "base_case_ids": ["dev-001"],
        "channels": ["C2", "C3", "C4"],
        "conditions": ["attack", "clean"],
        "configurations": ["D0_BASELINE"],
        "repeats": 1,
    }
    base.update(overrides)
    return base


def test_full_product_is_generated_from_data():
    spec = _spec(
        base_case_ids=["dev-001", "dev-002"],
        configurations=["D0_BASELINE", "D1_POLICY_GATE"],
        repeats=2,
    )
    trials = sched.generate_schedule(spec)
    # 2 bases x 3 channels x 2 conditions x 2 configs x 2 repeats
    assert len(trials) == 2 * 3 * 2 * 2 * 2
    cells = {
        (t.base_case_id, t.channel, t.condition, t.configuration, t.run_index) for t in trials
    }
    assert len(cells) == len(trials)  # every scheduled cell is distinct


def test_ids_are_globally_unique_and_well_formed():
    trials = sched.generate_schedule(_spec())
    assert len({t.logical_trial_id for t in trials}) == len(trials)
    for t in trials:
        assert t.logical_trial_id == (
            f"exp-fixed:unfrozen:mock-canned-v0:dev-001:"
            f"{t.channel}:{t.condition}:{t.configuration}:r{t.run_index}"
        )
        assert t.comparison_superblock_id == "exp-fixed:unfrozen:mock-canned-v0:dev-001:r1"


def test_schedule_index_is_dense_and_ordered():
    trials = sched.generate_schedule(_spec(base_case_ids=["dev-001", "dev-002"], repeats=2))
    assert [t.schedule_index for t in trials] == list(range(len(trials)))


def test_generation_is_deterministic_in_the_seed():
    a = sched.generate_schedule(_spec())
    b = sched.generate_schedule(_spec())
    assert [t.logical_trial_id for t in a] == [t.logical_trial_id for t in b]


def test_a_different_seed_changes_the_order_not_the_set():
    a = sched.generate_schedule(_spec(seed="one"))
    b = sched.generate_schedule(_spec(seed="two"))
    assert [t.logical_trial_id for t in a] != [t.logical_trial_id for t in b]
    assert {t.logical_trial_id for t in a} == {t.logical_trial_id for t in b}


def test_superblocks_are_contiguous_and_grouped_in_order():
    spec = _spec(base_case_ids=["dev-001", "dev-002"], repeats=2)
    trials = sched.generate_schedule(spec)
    groups = sched.superblock_groups(trials)
    # 2 bases x 2 repeats = 4 superblocks
    assert len(groups) == 4
    # each group holds exactly its 6 cells, all sharing the superblock id
    for sb_id, members in groups.items():
        assert len(members) == 6
        assert {m.comparison_superblock_id for m in members} == {sb_id}
    # contiguity: the schedule never interleaves two superblocks
    seen = []
    for t in trials:
        if not seen or seen[-1] != t.comparison_superblock_id:
            assert t.comparison_superblock_id not in seen, "superblock is not contiguous"
            seen.append(t.comparison_superblock_id)


def test_within_superblock_order_is_independent_of_superblock_position():
    """A superblock's internal cell order depends only on the seed and its own id,
    not on where the superblock landed in the overall shuffle."""
    one = sched.superblock_groups(sched.generate_schedule(_spec(base_case_ids=["dev-001"])))
    many = sched.superblock_groups(
        sched.generate_schedule(_spec(base_case_ids=["dev-001", "dev-002", "dev-003"]))
    )
    sb_id = next(iter(one))
    order_one = [(t.channel, t.condition, t.configuration) for t in one[sb_id]]
    order_many = [(t.channel, t.condition, t.configuration) for t in many[sb_id]]
    assert order_one == order_many


def test_duplicate_cell_fails_closed():
    with pytest.raises(ValueError):
        sched.generate_schedule(_spec(channels=["C2", "C2"]))


@pytest.mark.parametrize("missing", ["experiment_id", "seed", "base_case_ids", "repeats"])
def test_missing_required_key_fails_closed(missing):
    spec = _spec()
    del spec[missing]
    with pytest.raises(ValueError):
        sched.generate_schedule(spec)


@pytest.mark.parametrize("empty", ["base_case_ids", "channels", "conditions", "configurations"])
def test_empty_component_fails_closed(empty):
    with pytest.raises(ValueError):
        sched.generate_schedule(_spec(**{empty: []}))


def test_repeats_below_one_fails_closed():
    with pytest.raises(ValueError):
        sched.generate_schedule(_spec(repeats=0))


def test_different_experiment_ids_never_collide():
    """A6: the experiment id is a prefix of every derived id, so two runs with
    different experiment ids share no logical_trial_id or comparison_superblock_id,
    even with the same seed and components."""
    a = sched.generate_schedule(_spec(experiment_id="exp-a"))
    b = sched.generate_schedule(_spec(experiment_id="exp-b"))
    ids_a = {t.logical_trial_id for t in a}
    ids_b = {t.logical_trial_id for t in b}
    assert ids_a.isdisjoint(ids_b)
    sb_a = {t.comparison_superblock_id for t in a}
    sb_b = {t.comparison_superblock_id for t in b}
    assert sb_a.isdisjoint(sb_b)
    # same cardinality and structure, only the experiment prefix differs
    assert len(ids_a) == len(ids_b) == len(a)
    assert {i.split(":", 1)[1] for i in ids_a} == {i.split(":", 1)[1] for i in ids_b}
