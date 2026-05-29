from fastapi import FastAPI, Response

from models.inspection import InspectionPayload
from pdf import generate_pdf

app = FastAPI()


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
