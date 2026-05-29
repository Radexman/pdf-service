from pydantic import BaseModel, Field, model_validator
from enum import Enum


class ActionType(str, Enum):
    feeding_syrup = "feeding_syrup"
    feeding_candy = "feeding_candy"
    feeding_pollen = "feeding_pollen"
    feeding_water = "feeding_water"

    comb_added_drawn = "comb_added_drawn"
    comb_added_foundation = "comb_added_foundation"
    comb_removed_old = "comb_removed_old"
    comb_removed_drone = "comb_removed_drone"
    uncapping = "uncapping"

    super_added = "super_added"
    super_removed = "super_removed"
    division_board_moved = "division_board_moved"
    hive_expanded = "hive_expanded"

    honey_harvest = "honey_harvest"
    honey_frames_returned = "honey_frames_returned"

    queen_introduced = "queen_introduced"
    queen_removed = "queen_removed"
    queen_cell_added = "queen_cell_added"
    queen_cells_removed = "queen_cells_removed"
    swarm_caught = "swarm_caught"
    split_made = "split_made"

    treatment_oxalic_acid = "treatment_oxalic_acid"
    treatment_formic_acid = "treatment_formic_acid"
    treatment_apistan = "treatment_apistan"
    treatment_apivar = "treatment_apivar"
    treatment_other_varroa = "treatment_other_varroa"
    treatment_nosema = "treatment_nosema"
    treatment_other = "treatment_other"

    hive_cleaned = "hive_cleaned"
    hive_moved = "hive_moved"
    entrance_reduced = "entrance_reduced"
    entrance_opened = "entrance_opened"

    mouse_guard_added = "mouse_guard_added"
    mouse_guard_removed = "mouse_guard_removed"

    insulation_added = "insulation_added"
    insulation_removed = "insulation_removed"

    other = "other"


class ActionsData(BaseModel):
    selected: list[ActionType] = Field(
        default_factory=list, description="Performed beekeping actions"
    )
    other: str | None = Field(
        default=None, max_length=500, description="Custom beekeping action"
    )

    @model_validator(mode="after")
    def validate_other(self):
        has_other = ActionType.other in self.selected

        if has_other and not self.other:
            raise ValueError("'other' action requires description")

        if not has_other and self.other:
            raise ValueError("Custom description requires 'other' action")

        return self
