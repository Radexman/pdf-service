from pydantic import BaseModel, Field
from enum import Enum


class BroodType(str, Enum):
    eggs = "eggs"
    open = "open"
    capped = "capped"
    drone = "drone"


class BroodData(BaseModel):
    brood_types: list[BroodType] = Field(default_factory=list)
    brood_pattern: int = Field(ge=1, le=5, description="Brood compactness")
