from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

DocumentType = Literal["gst_certificate", "udyam_certificate", "pan_card"]


class DocumentExtractionResponse(BaseModel):
    fields: dict[str, str]
    warning: str | None
