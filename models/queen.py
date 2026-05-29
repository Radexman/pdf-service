from pydantic import BaseModel, Field, model_validator
from enum import Enum


class QueenStatus(str, Enum):
    seen = "seen"
    not_seen_brood_ok = "not_seen_brood_ok"
    missing = "missing"


class QueenMarkerColor(str, Enum):
    white = "white"
    yellow = "yellow"
    red = "red"
    green = "green"
    blue = "blue"


class QueenCellType(str, Enum):
    none = "none"
    emergency = "emergency"
    swarm = "swarm"
    supersedure = "supersedure"


class QueenData(BaseModel):
    queen_status: QueenStatus
    queen_marked: bool = Field(..., description="Whether the queen is marked")
    queen_marker_color: QueenMarkerColor | None = None
    queen_cells: QueenCellType
    queen_cells_count: int = Field(
        default=0, ge=0, le=50, description="Number of queen cells observed"
    )

    @model_validator(mode="after")
    def validate_marker(self):
        if self.queen_marked and self.queen_marker_color is None:
            raise ValueError("Marked queen must have a color")

        if not self.queen_marked and self.queen_marker_color is not None:
            raise ValueError("Unmarked queen cannot have a color")

        return self
