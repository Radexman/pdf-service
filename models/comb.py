from enum import Enum

from pydantic import BaseModel, Field, computed_field, model_validator

FRAME_TENTHS = 10
"""Frames are recorded in tenths: 5 = 50%, 1 = 10%. Matches how a frame is
eyeballed in the field — no fraction conversion with gloves on."""


class CombCondition(str, Enum):
    good = "good"
    old = "old"
    needs_replacement = "needs_replacement"


class CombState(str, Enum):
    foundation = "foundation"
    drawn = "drawn"


class FrameType(str, Enum):
    """Frame geometry -> capacity. Drives derived honey_kg."""

    wielkopolska = "wielkopolska"


FRAME_CAPACITY_KG: dict[FrameType, float] = {
    # Measured: a wielkopolska frame (360x260) full of capped honey.
    FrameType.wielkopolska: 2.25,
}


class HoneySufficiency(str, Enum):
    sufficient = "sufficient"
    moderate = "moderate"
    low = "low"
    none = "none"


SUFFICIENCY_LOW_FRAMES = 1.0
"""Below one full frame of stores the colony has no buffer for a rained-out
week — feeding trigger. Expressed in frames so it tracks frame_type."""

SUFFICIENCY_SUFFICIENT_KG = 10.0
"""Above this the colony carries stores into winter unaided."""


_WEAR_SEVERITY: dict[CombCondition, int] = {
    CombCondition.good: 0,
    CombCondition.old: 1,
    CombCondition.needs_replacement: 2,
}


class FrameComposition(BaseModel):
    position: int = Field(ge=1, description="Frame position in the box, 1-based")
    comb_state: CombState
    brood: int = Field(0, ge=0, le=FRAME_TENTHS, description="Brood, in tenths")
    honey: int = Field(0, ge=0, le=FRAME_TENTHS, description="Honey+nectar, tenths")
    pollen: int = Field(0, ge=0, le=FRAME_TENTHS, description="Pollen, in tenths")
    wear: CombCondition | None = Field(None, description="Comb wear for this frame")

    @model_validator(mode="after")
    def validate_frame(self):
        filled = self.brood + self.honey + self.pollen
        if filled > FRAME_TENTHS:
            raise ValueError(
                f"Frame {self.position}: brood+honey+pollen ({filled}) "
                f"exceeds {FRAME_TENTHS} tenths"
            )
        if self.comb_state is CombState.foundation and filled > 0:
            raise ValueError(
                f"Frame {self.position}: foundation cannot carry brood/honey/pollen"
            )
        return self

    @computed_field
    @property
    def empty(self) -> int:
        """Remainder tenths. Derived, never entered.

        Foundation reads as fully empty here; ``CombData`` keeps the two apart
        (drawn-and-empty is layable now, foundation is not).
        """
        return FRAME_TENTHS - (self.brood + self.honey + self.pollen)


class CombData(BaseModel):
    schema_version: int = Field(2, description="Payload schema discriminator")
    frame_type: FrameType = FrameType.wielkopolska
    slots: int | None = Field(None, ge=1, le=20)

    low_confidence: bool = Field(
        False,
        description="Rushed / rough estimate (e.g. giving a tour). "
        "Filtered out of trend analysis.",
    )

    frames: list[FrameComposition]

    @model_validator(mode="after")
    def validate_comb(self):
        if not self.frames:
            raise ValueError("Comb must have at least one frame")

        positions = [f.position for f in self.frames]
        if len(set(positions)) != len(positions):
            raise ValueError("Duplicate frame positions")

        if self.slots is not None:
            if len(self.frames) > self.slots:
                raise ValueError(
                    f"Frame count ({len(self.frames)}) exceeds box slots "
                    f"({self.slots})"
                )
            if any(p > self.slots for p in positions):
                raise ValueError("Frame position outside box slots")
        return self

    def _frames_equiv(self, tenths: int) -> float:
        return round(tenths / FRAME_TENTHS, 1)

    @computed_field
    @property
    def frame_capacity_kg(self) -> float:
        """Honey in one full frame of this type — the calibration behind
        honey_kg. Surfaced so the sheet can show its own arithmetic."""
        return FRAME_CAPACITY_KG[self.frame_type]

    @computed_field
    @property
    def honey_kg(self) -> float:
        return round(
            sum(f.honey for f in self.frames) / FRAME_TENTHS * self.frame_capacity_kg, 2
        )

    @computed_field
    @property
    def honey_stores(self) -> HoneySufficiency:
        kg = self.honey_kg
        if kg <= 0:
            return HoneySufficiency.none
        if kg < SUFFICIENCY_LOW_FRAMES * self.frame_capacity_kg:
            return HoneySufficiency.low
        if kg <= SUFFICIENCY_SUFFICIENT_KG:
            return HoneySufficiency.moderate
        return HoneySufficiency.sufficient

    @computed_field
    @property
    def brood_frames_equiv(self) -> float:
        """Full-frame equivalents of brood — development metric."""
        return self._frames_equiv(sum(f.brood for f in self.frames))

    @computed_field
    @property
    def honey_frames_equiv(self) -> float:
        return self._frames_equiv(sum(f.honey for f in self.frames))

    @computed_field
    @property
    def pollen_frames_equiv(self) -> float:
        return self._frames_equiv(sum(f.pollen for f in self.frames))

    @computed_field
    @property
    def empty_frames_equiv(self) -> float:
        """Drawn comb standing empty — laying room available right now.

        Foundation is excluded: it is not yet comb. See ``foundation_frames``.
        """
        return self._frames_equiv(
            sum(f.empty for f in self.frames if f.comb_state is CombState.drawn)
        )

    @computed_field
    @property
    def occupied_frames(self) -> int:
        return sum(1 for f in self.frames if f.brood or f.honey or f.pollen)

    @computed_field
    @property
    def foundation_frames(self) -> int:
        """Unbuilt frames — comb-drawing pace between inspections."""
        return sum(1 for f in self.frames if f.comb_state is CombState.foundation)

    @computed_field
    @property
    def comb_condition(self) -> CombCondition:
        """Hive-level wear = worst per-frame wear; ``good`` if none recorded."""
        worst = CombCondition.good
        for f in self.frames:
            if f.wear is not None and _WEAR_SEVERITY[f.wear] > _WEAR_SEVERITY[worst]:
                worst = f.wear
        return worst
