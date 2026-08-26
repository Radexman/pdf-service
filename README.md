# beehive-inspection-pdf-service

Renders a beekeeping inspection (**protokół przeglądu rodziny pszczelej**) to a
print-ready A4 PDF in Polish.

It is a small, **stateless** HTTP service: POST one complete inspection payload,
get back PDF bytes. No database, no file storage, no session state — the calling
app owns the data, this service owns the paper.

```
JSON payload  ──▶  Pydantic validation  ──▶  Jinja2 → HTML  ──▶  WeasyPrint → PDF
                   (models/)                 (templates/)        (pdf.py)
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness probe — `{"status": "ok"}` |
| `POST` | `/generate-pdf` | Inspection payload in, PDF bytes out |
| `GET` | `/docs` | Swagger UI (auto-generated, interactive) |
| `GET` | `/redoc` | ReDoc reference |
| `GET` | `/openapi.json` | OpenAPI schema |

`POST /generate-pdf` responds with `Content-Type: application/pdf` and a
`Content-Disposition` filename built from the payload meta, e.g.
`Pasieka Siek-Ul-12-Przeglad-8-2026-08-14.pdf`.

An invalid payload returns **422** with FastAPI's usual validation detail —
useful during app development, since every domain rule below is enforced here.

## Running it locally

Requires **Python 3.13** and, on Windows, the **GTK runtime** that WeasyPrint
needs for text layout (see [WeasyPrint's install docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html)).
On Linux the equivalent system libraries are listed in the [Dockerfile](Dockerfile).

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Then open <http://127.0.0.1:8000/docs>.

Smoke-test it against a fixture:

```powershell
curl.exe -X POST http://127.0.0.1:8000/generate-pdf `
  -H "Content-Type: application/json" `
  --data-binary "@mock/strong_colony_summer_flow.json" `
  -o out.pdf
```

`requirements.txt` is the runtime set; `requirements-dev.txt` adds pytest and the
`fastapi dev` CLI. Production runs `uvicorn main:app` in Docker (no `--reload`).

### Docker

```bash
docker build -t pdf-service .
docker run --rm -p 8000:8000 pdf-service
```

Then open <http://localhost:8000/docs> — **not** the `http://0.0.0.0:8000` that
uvicorn prints on startup. `0.0.0.0` means "bind every interface"; it is not a
browsable address and Chrome rejects it with `ERR_ADDRESS_INVALID`. There is
also no `/` route, so the bare host returns a 404 by design.

The image installs Pango/HarfBuzz and DejaVu fonts, which a bare `python:slim`
lacks — without them WeasyPrint cannot lay out text or draw the `✓` glyph. The
container honours a `PORT` env var so it drops straight onto Render/Railway.

PDFs rendered in the container differ slightly in size from local Windows ones:
the template's first-choice font (Segoe UI) does not exist on Linux, so DejaVu
is substituted. Both are valid; the layout is unchanged.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Two suites, both fast and offline:

- `tests/test_comb.py` — validation rules and the derived-field contract.
- `tests/test_template_render.py` — renders the Jinja template under
  `StrictUndefined` for every fixture in `mock/`, so a stale variable reference
  in the template fails the build instead of silently printing a blank.

## The payload

Top-level shape is `InspectionPayload` in [models/inspection.py](models/inspection.py),
with `extra="forbid"` — unknown keys are rejected rather than ignored. Sections:
`meta`, `weather` (optional), `queen`, `brood`, `colony`, `comb`, `actions`,
`health`, `notes`.

Working examples live in [mock/](mock/) and double as test fixtures:

| Fixture | Scenario |
|---|---|
| `strong_colony_summer_flow.json` | Strong colony, super added, full stores |
| `varroa_chalkbrood_swarm.json` | Swarm mood + varroa + chalkbrood |
| `varroa_heavy_dwv.json` | Weakened colony, heavy mite drop, DWV |

### How frames are recorded

The comb section is the part with real domain rules, so it's worth reading
before wiring up a client.

Each frame is recorded **in tenths** — `5` means the frame is 50% full of that
content, `1` means 10%. That matches how a frame gets eyeballed in the field.

```json
{ "position": 3, "comb_state": "drawn", "brood": 6, "honey": 2, "pollen": 2 }
```

- `brood + honey + pollen` may not exceed **10**; the remainder is `empty`.
- `comb_state` is `drawn` (built comb) or `foundation` (węza). Foundation may
  not carry any content.
- `position` is 1-based and must be unique. If `slots` (box capacity) is given,
  frame count and positions are checked against it.
- **The number of frames in the hive is `len(frames)`** — there is no separate
  count field, so it can never disagree with the list.

### Derived values — never sent, always computed

The point of per-frame recording is that the totals stop being a second thing to
enter (and get wrong). The service computes these and the PDF prints them:

| Field | Meaning |
|---|---|
| `honey_kg` | Honey in kg — honey tenths ÷ 10 × `frame_capacity_kg` |
| `honey_stores` | Sufficiency band, see below |
| `brood_frames_equiv` etc. | Full-frame equivalents as decimals — `4.3` frames of brood |
| `empty_frames_equiv` | Drawn comb standing empty — **excludes foundation** |
| `foundation_frames` | Unbuilt frames — comb-drawing pace between inspections |
| `comb_condition` | Hive-level wear = the worst per-frame `wear` |
| `occupied_frames` | Frames carrying anything at all |

`frame_capacity_kg` comes from `frame_type`. A full *ramka wielkopolska* of
capped honey is calibrated at **2.25 kg** in
[models/comb.py](models/comb.py) — that constant is the basis of every honey
figure on the sheet, so re-measure it before trusting the numbers in a new
apiary.

`honey_stores` bands, rendered as Polish phrases from
[constants/labels.py](constants/labels.py):

| kg | Band | Sheet reads |
|---|---|---|
| `0` | `none` | brak zapasów |
| below one full frame (2.25 kg) | `low` | małe zapasy |
| up to 10 kg | `moderate` | umiarkowane zapasy |
| above 10 kg | `sufficient` | wystarczające zapasy |

The low edge is derived from frame capacity rather than hard-coded, so adding a
frame type with different geometry moves the feeding trigger with it.

## Layout of the repo

```
main.py            FastAPI app — routes only
pdf.py             Jinja environment, filters, HTML → PDF
models/            Pydantic payload sections + validation + derived fields
constants/         Polish label maps (actions, health, weather, comb, stores)
templates/         inspection.html — the whole sheet, print CSS inline
mock/              Example payloads, also used as test fixtures
tests/
```

Polish labels are **not** hard-coded in the template. They live in `constants/`
and reach the page through Jinja filters registered in
[pdf.py](pdf.py) (`action_label`, `health_label`, `weather_label`,
`comb_condition_label`, `honey_stores_label`, and `dec` for the Polish decimal
comma). Adding a new enum value means adding its label there too, or the raw key
prints.

Free-form fields (`notes`, `actions.other`, `health.other`) are user input and
are HTML-escaped via Jinja autoescaping.
