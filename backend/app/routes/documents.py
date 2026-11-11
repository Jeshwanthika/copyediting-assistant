"""Errors & solutions PDFs.

Everyone signed in can list and read them. Only leads can upload, rename,
replace or delete them.
"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import current_user, require_lead
from app.config import settings
from app.database import get_db
from app.models import Document, User
from app.schemas.document import DocumentRead, DocumentUpdate
from app.services import document_service
from app.services.document_service import DocumentError

router = APIRouter(prefix="/documents", tags=["errors & solutions"])


def _document_or_404(db: Session, document_id: int) -> Document:
    document = document_service.get_document(db, document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Document {document_id} not found")
    return document


async def _read_upload(file: UploadFile) -> bytes:
    # Read one byte past the limit so an oversized file is rejected without
    # holding an unbounded amount in memory.
    limit = settings.max_document_mb * 1024 * 1024
    content = await file.read(limit + 1)
    await file.close()
    return content


@router.get("", response_model=list[DocumentRead], dependencies=[Depends(current_user)])
def list_documents(db: Session = Depends(get_db)):
    return document_service.list_documents(db)


@router.get("/{document_id}", response_model=DocumentRead, dependencies=[Depends(current_user)])
def get_document(document_id: int, db: Session = Depends(get_db)):
    return _document_or_404(db, document_id)


@router.get("/{document_id}/file", dependencies=[Depends(current_user)])
def get_document_file(document_id: int, download: bool = False, db: Session = Depends(get_db)):
    """The PDF itself. Shown inline (in the browser's PDF viewer) unless ?download=true."""
    document = _document_or_404(db, document_id)
    path = document_service.file_path(document)
    if not path.is_file():
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "The PDF file is missing on the server. Ask a lead to re-upload it."
        )
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=document.original_filename,
        content_disposition_type="attachment" if download else "inline",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    description: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(require_lead),
):
    """Add a PDF (multipart form: file, optional title and description)."""
    content = await _read_upload(file)
    try:
        return document_service.create_document(
            db, content, file.filename, title=title, description=description, uploaded_by=user
        )
    except DocumentError as error:
        raise HTTPException(422, str(error)) from error


@router.patch("/{document_id}", response_model=DocumentRead, dependencies=[Depends(require_lead)])
def update_document(document_id: int, data: DocumentUpdate, db: Session = Depends(get_db)):
    document = _document_or_404(db, document_id)
    try:
        return document_service.update_details(
            db, document, title=data.title, description=data.description, sort_order=data.sort_order
        )
    except DocumentError as error:
        raise HTTPException(422, str(error)) from error


@router.put(
    "/{document_id}/file", response_model=DocumentRead, dependencies=[Depends(require_lead)]
)
async def replace_document_file(
    document_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """Replace the PDF but keep the title, description and position."""
    document = _document_or_404(db, document_id)
    content = await _read_upload(file)
    try:
        return document_service.replace_file(db, document, content, file.filename)
    except DocumentError as error:
        raise HTTPException(422, str(error)) from error


@router.delete(
    "/{document_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_lead)]
)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document_service.delete_document(db, _document_or_404(db, document_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
