"""v1.1 per-frame composition model — validation + derived contract.

Frames are recorded in tenths (5 = 50%). Covers SPEC §4 (derived contract),
§5 (validation rules) and §10 (the real-data proof that honey on brood frames
is now visible).
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from models.comb import (
    CombData,
    CombState,
    CombCondition,
    FrameComposition,
    FrameType,
    FRAME_CAPACITY_KG,
    FRAME_TENTHS,
    HoneySufficiency,
    SUFFICIENCY_SUFFICIENT_KG,
)
from models.inspection import InspectionPayload

MOCK_DIR = Path(__file__).resolve().parent.parent / "mock"

MOCK_NAMES = [
    "varroa_chalkbrood_swarm.json",
    "varroa_heavy_dwv.json",
    "strong_colony_summer_flow.json",
]

CAPACITY = FRAME_CAPACITY_KG[FrameType.wielkopolska]


def frame(position=1, comb_state=CombState.drawn, **kw):
    return FrameComposition(position=position, comb_state=comb_state, **kw)


# --- §5 Frame validation -------------------------------------------------


def test_frame_rejects_overfilled():
    with pytest.raises(ValidationError, match="exceeds 10 tenths"):
        frame(brood=8, honey=2, pollen=1)


def test_frame_accepts_exactly_full():
    f = frame(brood=8, honey=1, pollen=1)
    assert f.empty == 0


def test_foundation_cannot_carry_content():
    with pytest.raises(ValidationError, match="foundation cannot carry"):
        frame(comb_state=CombState.foundation, honey=1)


def test_foundation_empty_is_valid():
    f = frame(comb_state=CombState.foundation)
    assert f.empty == FRAME_TENTHS


def test_empty_is_the_remainder():
    assert frame(brood=3, honey=1).empty == 6


def test_half_frame_reads_as_five_tenths():
    """The point of the tenths scale: 5 == 50%."""
    assert frame(honey=5).honey / FRAME_TENTHS == 0.5


@pytest.mark.parametrize("field", ["brood", "honey", "pollen"])
def test_tenth_bounds(field):
    with pytest.raises(ValidationError):
        frame(**{field: 11})


def test_position_must_be_positive():
    with pytest.raises(ValidationError):
        frame(position=0)


# --- §5 Comb validation --------------------------------------------------


def test_comb_requires_a_frame():
    with pytest.raises(ValidationError, match="at least one frame"):
        CombData(frames=[])


def test_duplicate_positions_rejected():
    with pytest.raises(ValidationError, match="Duplicate frame positions"):
        CombData(frames=[frame(1, honey=1), frame(1, honey=2)])


def test_frame_count_exceeding_slots_rejected():
    with pytest.raises(ValidationError, match="exceeds box slots"):
        CombData(slots=1, frames=[frame(1, honey=1), frame(2, honey=1)])


def test_position_outside_slots_rejected():
    with pytest.raises(ValidationError, match="outside box slots"):
        CombData(slots=2, frames=[frame(5, honey=1)])


# --- §4 Derived contract -------------------------------------------------


def test_honey_kg_derives_from_tenths():
    # 4 full frames of honey = 40 tenths -> 4 * capacity
    comb = CombData(
        frame_type=FrameType.wielkopolska,
        frames=[frame(i, honey=FRAME_TENTHS) for i in range(1, 5)],
    )
    assert comb.honey_kg == pytest.approx(4 * CAPACITY)


def test_half_a_frame_is_half_the_capacity():
    comb = CombData(frames=[frame(1, honey=5)])
    # honey_kg is rounded to 2 decimals for display, hence the tolerance.
    assert comb.honey_kg == pytest.approx(CAPACITY / 2, abs=0.005)


@pytest.mark.parametrize(
    "honey_tenths, expected",
    [
        (0, HoneySufficiency.none),  # 0 kg      -> brak zapasów
        (1, HoneySufficiency.low),  # 0.225 kg  -> below one full frame
        (9, HoneySufficiency.low),  # 2.025 kg  -> still below one frame
        (10, HoneySufficiency.moderate),  # 2.25 kg  -> exactly one frame
        (44, HoneySufficiency.moderate),  # 9.9 kg   -> under the winter mark
        (45, HoneySufficiency.sufficient),  # 10.125 kg -> over 10 kg
    ],
)
def test_honey_stores_thresholds(honey_tenths, expected):
    # Spread the requested tenths across single-tenth honey frames.
    frames = [frame(i + 1, honey=1) for i in range(honey_tenths)] or [frame(1)]
    comb = CombData(frames=frames)
    assert comb.honey_stores is expected


def test_low_threshold_is_one_full_frame():
    """The 'feeding trigger' band is derived from frame capacity, not a
    hard-coded kg figure, so it stays correct for other frame types."""
    just_under = CombData(frames=[frame(1, honey=9)])
    exactly_one = CombData(frames=[frame(1, honey=FRAME_TENTHS)])
    assert just_under.honey_kg < CAPACITY
    assert just_under.honey_stores is HoneySufficiency.low
    assert exactly_one.honey_kg == pytest.approx(CAPACITY)
    assert exactly_one.honey_stores is HoneySufficiency.moderate


def test_sufficient_band_starts_above_ten_kg():
    comb = CombData(frames=[frame(i, honey=FRAME_TENTHS) for i in range(1, 6)])
    assert comb.honey_kg > SUFFICIENCY_SUFFICIENT_KG
    assert comb.honey_stores is HoneySufficiency.sufficient


def test_frames_equiv_are_decimals():
    comb = CombData(
        frames=[
            frame(1, brood=8, honey=1, pollen=1),
            frame(2, brood=5, honey=4, pollen=1),
            frame(3, honey=10),
        ]
    )
    assert comb.brood_frames_equiv == pytest.approx(1.3)
    assert comb.honey_frames_equiv == pytest.approx(1.5)
    assert comb.pollen_frames_equiv == pytest.approx(0.2)


def test_empty_equiv_excludes_foundation():
    """Drawn-and-empty is layable room; foundation is not comb yet. They must
    not be pooled into one 'puste' figure."""
    comb = CombData(
        frames=[
            frame(1, brood=6),  # 4 tenths of drawn comb standing empty
            frame(2),  # 10 tenths drawn, empty
            frame(3, comb_state=CombState.foundation),  # not counted
        ]
    )
    assert comb.empty_frames_equiv == pytest.approx(1.4)
    assert comb.foundation_frames == 1


def test_occupied_and_foundation_counts():
    comb = CombData(
        frames=[
            frame(1, brood=4),
            frame(2),  # drawn, empty
            frame(3, comb_state=CombState.foundation),
        ]
    )
    assert comb.occupied_frames == 1
    assert comb.foundation_frames == 1


def test_comb_condition_is_worst_wear():
    comb = CombData(
        frames=[
            frame(1, honey=10, wear=CombCondition.good),
            frame(2, brood=10, wear=CombCondition.needs_replacement),
            frame(3, pollen=2, wear=CombCondition.old),
        ]
    )
    assert comb.comb_condition is CombCondition.needs_replacement


def test_comb_condition_defaults_good_without_wear():
    comb = CombData(frames=[frame(1, honey=4)])
    assert comb.comb_condition is CombCondition.good


def test_computed_fields_serialize_for_template():
    # generate_pdf() renders payload.model_dump(mode="json"); computed fields
    # must appear there or the Jinja template would see undefined values.
    comb = CombData(frames=[frame(1, brood=8, honey=1, pollen=1)])
    dumped = comb.model_dump(mode="json")
    for key in (
        "frame_capacity_kg",
        "honey_kg",
        "honey_stores",
        "comb_condition",
        "brood_frames_equiv",
        "honey_frames_equiv",
        "pollen_frames_equiv",
        "empty_frames_equiv",
        "foundation_frames",
        "occupied_frames",
    ):
        assert key in dumped, key
    assert dumped["honey_stores"] == "low"  # 1 tenth honey -> 0.23 kg


# --- §10 Real-data proof: honey on brood frames is now visible -----------


def test_honey_on_brood_frames_is_no_longer_invisible():
    """The inspection #5 / hive #1 failure: 0 kg recorded while brood frames
    carried honey arcs. In v1.0 that honey was uncountable. Encode the arcs
    and assert the model now sees them."""
    brood_frames_with_honey_arc = [
        frame(i, brood=8, honey=1, pollen=1) for i in range(1, 8)
    ]
    comb = CombData(frames=brood_frames_with_honey_arc)

    assert comb.honey_kg > 0, "honey on brood frames must be counted"
    assert comb.honey_frames_equiv == pytest.approx(0.7)
    assert comb.honey_stores is not HoneySufficiency.none


# --- Mock fixtures parse under the new schema ----------------------------


@pytest.mark.parametrize("name", MOCK_NAMES)
def test_mock_payloads_valid(name):
    data = json.loads((MOCK_DIR / name).read_text(encoding="utf-8"))
    payload = InspectionPayload.model_validate(data)
    assert payload.comb.honey_kg > 0
    assert payload.comb.frames  # non-empty


def test_strong_colony_fixture_reads_as_a_strong_colony():
    """The fixture is the end-to-end proof of the new flow: a full super of
    honey has to land in the top sufficiency band on its own."""
    data = json.loads(
        (MOCK_DIR / "strong_colony_summer_flow.json").read_text(encoding="utf-8")
    )
    comb = InspectionPayload.model_validate(data).comb

    assert comb.honey_stores is HoneySufficiency.sufficient
    assert comb.honey_kg > SUFFICIENCY_SUFFICIENT_KG
    assert comb.brood_frames_equiv >= 6.0
    assert comb.foundation_frames == 1
    assert comb.comb_condition is CombCondition.old
