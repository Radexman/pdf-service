"""HTTP surface: the routes as a client actually meets them."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app

MOCK_DIR = Path(__file__).resolve().parent.parent / "mock"

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_root_redirects_to_docs():
    """A bare host hit (e.g. the Render URL) lands on the docs, not a 404."""
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"] == "/docs"


def test_root_redirect_target_is_reachable():
    r = client.get("/", follow_redirects=True)
    assert r.status_code == 200


def test_generate_pdf_rejects_get():
    """Why / cannot redirect to /generate-pdf: it is POST-only."""
    assert client.get("/generate-pdf").status_code == 405


@pytest.mark.parametrize(
    "name",
    [
        "varroa_chalkbrood_swarm.json",
        "varroa_heavy_dwv.json",
        "strong_colony_summer_flow.json",
    ],
)
def test_generate_pdf_returns_a_pdf(name):
    data = json.loads((MOCK_DIR / name).read_text(encoding="utf-8"))
    r = client.post("/generate-pdf", json=data)

    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF-")
    assert ".pdf" in r.headers["content-disposition"]


def test_out_of_range_tenths_rejected():
    data = json.loads((MOCK_DIR / "varroa_heavy_dwv.json").read_text(encoding="utf-8"))
    data["comb"]["frames"][0]["honey"] = 12  # scale is 0-10
    assert client.post("/generate-pdf", json=data).status_code == 422
