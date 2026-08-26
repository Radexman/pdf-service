from models.comb import CombCondition, HoneySufficiency
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

# Derived at render time from comb.honey_kg — never entered in the field.
HONEY_STORES_LABELS: dict[str, str] = {
    HoneySufficiency.none: "brak zapasów",
    HoneySufficiency.low: "małe zapasy",
    HoneySufficiency.moderate: "umiarkowane zapasy",
    HoneySufficiency.sufficient: "wystarczające zapasy",
}
