from pydantic import BaseModel, Field, model_validator
from enum import Enum


class HealthCondition(str, Enum):
    dwv = "dwv"
    foulbrood = "foulbrood"
    dysentery = "dysentery"
    varroa = "varroa"
    chalkbrood = "chalkbrood"
    acarine = "acarine"
    wax_moth = "wax_moth"
    other = "other"


class HealthData(BaseModel):
    conditions: list[HealthCondition] = Field(
        default_factory=list, description="Observed health conditions"
    )
    varroa_drop_count: int | None = Field(
        default=None, ge=0, le=500, description="Varroa mite drop count per 24h"
    )
    other: str | None = Field(
        default=None, max_length=500, description="Custom health condition description"
    )

    @model_validator(mode="after")
    def validate_conditions(self):
        has_varroa = HealthCondition.varroa in self.conditions
        has_other = HealthCondition.other in self.conditions

        if has_varroa and self.varroa_drop_count is None:
            raise ValueError("Varroa condition requires mite drop count")

        if not has_varroa and self.varroa_drop_count is not None:
            raise ValueError("Varroa count requires varroa condition")

        if has_other and not (self.other and self.other.strip()):
            raise ValueError("'other' condition requires description")

        if not has_other and self.other and self.other.strip():
            raise ValueError("Custom description requires 'other' condition")

        return self
