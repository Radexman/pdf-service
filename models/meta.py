from datetime import date

from pydantic import BaseModel, Field


class InspectionMeta(BaseModel):
    """Identity / header data printed at the top of the inspection sheet.

    Owned by the calling backend (the main Pasieka App) and sent in the POST
    body; the PDF service stays stateless.
    """

    apiary_name: str = Field(..., max_length=120, description="Apiary name")
    beekeeper_name: str = Field(..., max_length=120, description="Beekeeper full name")
    veterinary_number: str = Field(
        ..., max_length=60, description="Veterinary identification number (WNI)"
    )
    hive_number: str = Field(..., max_length=30, description="Hive number / label")
    inspection_number: str = Field(
        ..., max_length=30, description="Sequential inspection number"
    )
    inspection_date: date = Field(
        default_factory=date.today, description="Date of the inspection"
    )
