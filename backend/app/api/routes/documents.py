from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.ocr.base import OCRProvider
from app.ocr.extraction import extract_fields
from app.ocr.factory import get_ocr_provider
from app.schemas.document import DocumentExtractionResponse, DocumentType

router = APIRouter(prefix="/documents", tags=["documents"])

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


@router.post("/extract", response_model=DocumentExtractionResponse)
async def extract_document(
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    ocr_provider: OCRProvider = Depends(get_ocr_provider),
) -> DocumentExtractionResponse:
    """Runs OCR + deterministic field extraction on an uploaded document
    image and returns what was found -- nothing is persisted here. The
    caller (Onboarding) is responsible for showing these fields to the
    user for review/edit before saving them anywhere; that mandatory
    human-review step is enforced by this route simply not taking a DB
    session at all.
    """
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{file.content_type}'. Upload a JPEG or PNG image.",
        )

    image_bytes = await file.read()
    if len(image_bytes) > _MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=422, detail="File too large (max 10MB).")

    raw_text = ocr_provider.extract_text(image_bytes)
    result = extract_fields(raw_text, document_type)
    return DocumentExtractionResponse(fields=result.fields, warning=result.warning)
