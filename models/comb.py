from pydantic import BaseModel, Field, model_validator
from enum import Enum


class CombCondition(str, Enum):
    good = "good"
    old = "old"
    needs_replacement = "needs_replacement"


class CombData(BaseModel):
    frames_brood: int = Field(ge=0, description="Frames with brood")
    frames_honey: int = Field(ge=0, description="Frames with honey")
    frames_pollen: int = Field(ge=0, description="Frames with pollen")
    frames_empty: int = Field(ge=0, description="Empty frames ready for use")
    comb_condition: CombCondition

    @model_validator(mode="after")
    def validate_frames(self):
        total = (
            self.frames_brood
            + self.frames_honey
            + self.frames_pollen
            + self.frames_empty
        )

        if total <= 0:
            raise ValueError("Hive must have at least one frame counted")

        return self
