from pydantic import BaseModel, ConfigDict, Field

from .meta import InspectionMeta
from .weather import WeatherData
from .queen import QueenData
from .brood import BroodData
from .colony import ColonyData
from .comb import CombData
from .actions import ActionsData
from .health import HealthData


class InspectionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: InspectionMeta
    weather: WeatherData | None = None
    queen: QueenData
    brood: BroodData
    colony: ColonyData
    comb: CombData
    actions: ActionsData = Field(default_factory=ActionsData)
    health: HealthData
    notes: str | None = Field(
        default=None, max_length=2000, description="Free-form inspection notes"
    )
