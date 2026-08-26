from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse

from models.inspection import InspectionPayload
from pdf import generate_pdf

app = FastAPI()


@app.get("/", include_in_schema=False)
def root():
    """Land on the API docs instead of a bare 404.

    /generate-pdf is POST-only, so it cannot be the redirect target — a browser
    GET would hit 405.
    """
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate-pdf")
def generate_pdf_endpoint(payload: InspectionPayload):
    pdf_bytes = generate_pdf(payload)
    filename = (
        f"{payload.meta.apiary_name}-Ul-{payload.meta.hive_number}"
        f"-Przeglad-{payload.meta.inspection_number}-{payload.meta.inspection_date}.pdf"
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
