from models.comb import CombCondition
from models.queen import QueenMarkerColor

# Polish labels previously hard-coded inside the Jinja template.
QUEEN_MARKER_COLOR_LABELS: dict[str, str] = {
    QueenMarkerColor.white: "biały",
    QueenMarkerColor.yellow: "żółty",
    QueenMarkerColor.red: "czerwony",
    QueenMarkerColor.green: "zielony",
    QueenMarkerColor.blue: "niebieski",
}

COMB_CONDITION_LABELS: dict[str, str] = {
    CombCondition.good: "dobry",
    CombCondition.old: "stare plastry",
    CombCondition.needs_replacement: "potrzeba wymiany",
}
