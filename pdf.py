from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from constants.actions import ACTION_LABELS
from constants.health import HEALTH_LABELS
from constants.labels import (
    COMB_CONDITION_LABELS,
    HONEY_STORES_LABELS,
    QUEEN_MARKER_COLOR_LABELS,
)
from constants.weather import WEATHER_CODES
from models.inspection import InspectionPayload

BASE_DIR = Path(__file__).parent

env = Environment(
    loader=FileSystemLoader(str(BASE_DIR / "templates")),
    # notes / actions.other / health.other are free-form user input -> escape them.
    autoescape=select_autoescape(["html"]),
)
env.filters["action_label"] = lambda k: ACTION_LABELS.get(k, k)
env.filters["health_label"] = lambda k: HEALTH_LABELS.get(k, k)
env.filters["weather_label"] = lambda c: WEATHER_CODES.get(c, "—")
env.filters["queen_color_label"] = lambda k: QUEEN_MARKER_COLOR_LABELS.get(k, k)
env.filters["comb_condition_label"] = lambda k: COMB_CONDITION_LABELS.get(k, k)
env.filters["honey_stores_label"] = lambda k: HONEY_STORES_LABELS.get(k, k)
# Polish decimal separator; trims the trailing ".0" on whole frames.
env.filters["dec"] = lambda v: f"{v:g}".replace(".", ",")


def generate_pdf(payload: InspectionPayload) -> bytes:
    """Render the inspection sheet to PDF bytes.

    ``mode="json"`` serializes enums to their string values and the date to an
    ISO string, so dict-based label lookups and ``{% if x == 'seen' %}`` checks
    in the template work as expected.
    """
    template = env.get_template("inspection.html")
    html = template.render(**payload.model_dump(mode="json"))
    return HTML(string=html).write_pdf()
