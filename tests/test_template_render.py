"""Render the Jinja template (no WeasyPrint) to prove every variable the
template references still resolves after honey moved colony.* -> comb.*.

StrictUndefined turns any missing variable into an error, so a stale
``colony.honey_stores`` reference would fail this test instead of silently
rendering blank.
"""

import json
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from constants.actions import ACTION_LABELS
from constants.health import HEALTH_LABELS
from constants.labels import (
    COMB_CONDITION_LABELS,
    HONEY_STORES_LABELS,
    QUEEN_MARKER_COLOR_LABELS,
)
from constants.weather import WEATHER_CODES
from models.inspection import InspectionPayload

BASE = Path(__file__).resolve().parent.parent
MOCK_DIR = BASE / "mock"


def _env():
    env = Environment(
        loader=FileSystemLoader(str(BASE / "templates")),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
    )
    env.filters["action_label"] = lambda k: ACTION_LABELS.get(k, k)
    env.filters["health_label"] = lambda k: HEALTH_LABELS.get(k, k)
    env.filters["weather_label"] = lambda c: WEATHER_CODES.get(c, "—")
    env.filters["queen_color_label"] = lambda k: QUEEN_MARKER_COLOR_LABELS.get(k, k)
    env.filters["comb_condition_label"] = lambda k: COMB_CONDITION_LABELS.get(k, k)
    env.filters["honey_stores_label"] = lambda k: HONEY_STORES_LABELS.get(k, k)
    env.filters["dec"] = lambda v: f"{v:g}".replace(".", ",")
    return env


MOCK_NAMES = [
    "varroa_chalkbrood_swarm.json",
    "varroa_heavy_dwv.json",
    "strong_colony_summer_flow.json",
]


def _render(name):
    data = json.loads((MOCK_DIR / name).read_text(encoding="utf-8"))
    payload = InspectionPayload.model_validate(data)
    html = (
        _env().get_template("inspection.html").render(**payload.model_dump(mode="json"))
    )
    return payload, html


@pytest.mark.parametrize("name", MOCK_NAMES)
def test_template_renders_with_new_model(name):
    payload, html = _render(name)

    # Derived honey figures reach the page from comb.*, not colony.*
    assert f"{payload.comb.honey_kg:g}".replace(".", ",") in html
    assert "kg" in html


@pytest.mark.parametrize("name", MOCK_NAMES)
def test_frame_equivalents_render_as_polish_decimals(name):
    payload, html = _render(name)
    comb = payload.comb

    for value in (comb.brood_frames_equiv, comb.honey_frames_equiv):
        assert f"{value:g}".replace(".", ",") in html
    assert "." not in f"{comb.brood_frames_equiv:g}".replace(".", ",")
