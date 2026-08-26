from pydantic import BaseModel, Field
from enum import Enum


class ColonyBehavior(str, Enum):
    calm = "calm"
    nervous = "nervous"
    aggressive = "aggressive"
    swarm_mood = "swarm_mood"


class HiveSpace(str, Enum):
    ok = "ok"
    tight = "tight"
    loose = "loose"
    added_super = "added_super"


class ColonyData(BaseModel):
    frames_covered: int = Field(ge=0, le=20, description="Frames covered by bees")
    behavior: ColonyBehavior
    hive_space: HiveSpace
