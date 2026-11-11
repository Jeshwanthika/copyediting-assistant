"""The "Errors & solutions" PDF library: store, list, replace and delete PDFs.

Files live on disk in settings.resolved_documents_dir under a random name; the
database row keeps the title, description and original file name. Only PDFs are
accepted (checked by their first bytes, not just the file name).
"""
import re
import secrets
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import SEED_DIR, settings
from app.models import Document, User

PDF_MAGIC = b"%PDF-"


class DocumentError(Exception):
    """The upload was rejected. The message is safe to show."""


def documents_dir() -> Path:
    path = settings.resolved_documents_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def file_path(document: Document) -> Path:
    return documents_dir() / document.stored_name


def validate_pdf(content: bytes) -> None:
    limit = settings.max_document_mb * 1024 * 1024
    if not content:
        raise DocumentError("The file is empty.")
    if len(content) > limit:
        raise DocumentError(f"The file is larger than {settings.max_document_mb} MB.")
    if not content[:1024].lstrip().startswith(PDF_MAGIC):
        raise DocumentError("Only PDF files can be uploaded.")


def safe_filename(name: str | None) -> str:
    """Keep only the base name with ordinary characters, always ending in .pdf."""
    base = Path(name or "document.pdf").name
    base = re.sub(r"[^A-Za-z0-9._ ()-]+", "_", base).strip(" ._") or "document"
    if not base.lower().endswith(".pdf"):
        base += ".pdf"
    return base[:200]


def title_from_filename(name: str) -> str:
    stem = Path(name).stem
    return re.sub(r"[_-]+", " ", stem).strip().capitalize() or "Untitled document"


def _write(content: bytes) -> str:
    stored = f"{secrets.token_hex(16)}.pdf"
    (documents_dir() / stored).write_bytes(content)
    return stored


def _remove_file(stored_name: str) -> None:
    try:
        (documents_dir() / stored_name).unlink()
    except FileNotFoundError:
        pass


def list_documents(db: Session) -> list[Document]:
    return list(db.scalars(select(Document).order_by(Document.sort_order, Document.id)))


def get_document(db: Session, document_id: int) -> Document | None:
    return db.get(Document, document_id)


def create_document(
    db: Session,
    content: bytes,
    filename: str | None,
    title: str | None = None,
    description: str | None = None,
    uploaded_by: User | None = None,
) -> Document:
    validate_pdf(content)
    original = safe_filename(filename)
    next_order = (db.scalar(select(func.max(Document.sort_order))) or 0) + 1
    document = Document(
        title=(title or "").strip() or title_from_filename(original),
        description=(description or "").strip() or None,
        original_filename=original,
        stored_name=_write(content),
        size_bytes=len(content),
        sort_order=next_order,
        uploaded_by_id=uploaded_by.id if uploaded_by else None,
    )
    db.add(document)
    db.commit()
    return document


def update_details(
    db: Session,
    document: Document,
    title: str | None = None,
    description: str | None = None,
    sort_order: int | None = None,
) -> Document:
    if title is not None:
        if not title.strip():
            raise DocumentError("The title cannot be blank.")
        document.title = title.strip()
    if description is not None:
        document.description = description.strip() or None
    if sort_order is not None:
        document.sort_order = sort_order
    db.commit()
    return document


def replace_file(
    db: Session, document: Document, content: bytes, filename: str | None
) -> Document:
    validate_pdf(content)
    old = document.stored_name
    document.stored_name = _write(content)
    document.original_filename = safe_filename(filename)
    document.size_bytes = len(content)
    db.commit()
    _remove_file(old)
    return document


def delete_document(db: Session, document: Document) -> None:
    stored = document.stored_name
    db.delete(document)
    db.commit()
    _remove_file(stored)


def seed_documents(db: Session, folder: Path = SEED_DIR / "documents") -> int:
    """Add every PDF in data/seed/documents/ that is not in the library yet.

    A PDF counts as already added when a document with the same original file
    name exists. Returns how many were added.
    """
    if not folder.is_dir():
        return 0
    existing = {d.original_filename for d in db.scalars(select(Document))}
    added = 0
    for path in sorted(folder.glob("*.pdf")) + sorted(folder.glob("*.PDF")):
        name = safe_filename(path.name)
        if name in existing:
            continue
        try:
            create_document(db, path.read_bytes(), path.name)
        except DocumentError as error:
            print(f"Skipped {path.name}: {error}")
            continue
        existing.add(name)
        added += 1
    return added
