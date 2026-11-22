"""
Documents API Router
Multi-file upload, encrypted storage, file streaming for preview, and deletion.
Strict owner checks on every endpoint (IDOR protected).
"""

from io import BytesIO
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.models import AuditLog, Document, User
from app.db.session import get_db
from app.schemas.document import DocumentOut
from app.services.documents.storage import (
    delete_stored_file,
    read_decrypted_file,
    sanitize_filename,
    save_encrypted_file,
    validate_file_content,
)
from app.services.extraction.pipeline import run_document_extraction_pipeline

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=List[DocumentOut], status_code=status.HTTP_201_CREATED)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    financial_year: str = Form("2025-26"),
    doc_type: Optional[str] = Form("other"),
    password: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Uploads one or multiple documents.
    Validates MIME type & size, encrypts file at rest, and initiates extraction pipeline.
    """
    created_docs: List[Document] = []

    for file in files:
        data = await file.read()
        sanitized_name = sanitize_filename(file.filename or "uploaded_document")
        mime = validate_file_content(data, sanitized_name)

        storage_path, file_hash = save_encrypted_file(data, current_user.id, sanitized_name)

        # Check for duplicate document
        existing = db.query(Document).filter(
            Document.user_id == current_user.id,
            Document.file_hash == file_hash,
        ).first()

        doc_record = Document(
            user_id=current_user.id,
            financial_year=financial_year,
            file_name=sanitized_name,
            file_type=mime,
            file_size=len(data),
            storage_path=storage_path,
            file_hash=file_hash,
            doc_type=doc_type or "other",
            status="uploaded",
        )
        db.add(doc_record)
        db.flush()

        audit = AuditLog(
            user_id=current_user.id,
            action="DOCUMENT_UPLOADED",
            details={"file_name": sanitized_name, "size": len(data), "doc_type": doc_type},
        )
        db.add(audit)
        created_docs.append(doc_record)

        # Trigger extraction pipeline
        background_tasks.add_task(run_document_extraction_pipeline, doc_record.id, db, password)

    db.commit()
    for d in created_docs:
        db.refresh(d)

    return created_docs


@router.get("", response_model=List[DocumentOut])
def list_user_documents(
    financial_year: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists all uploaded documents for authenticated user."""
    query = db.query(Document).filter(Document.user_id == current_user.id)
    if financial_year:
        query = query.filter(Document.financial_year == financial_year)
    return query.order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document_details(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Gets metadata and extraction status of a specific document."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return doc


@router.get("/{document_id}/file")
@router.get("/{document_id}/view")
def stream_decrypted_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Streams decrypted document file content for in-browser side-by-side preview.
    Protected by owner-check (IDOR secure).
    """
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    try:
        raw_bytes = read_decrypted_file(doc.storage_path)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not read file: {e}")

    return StreamingResponse(
        BytesIO(raw_bytes),
        media_type=doc.file_type,
        headers={"Content-Disposition": f'inline; filename="{doc.file_name}"'},
    )


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes document, stored encrypted file, and cascade-removes extracted fields."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    delete_stored_file(doc.storage_path)
    db.delete(doc)

    audit = AuditLog(user_id=current_user.id, action="DOCUMENT_DELETED", details={"file_name": doc.file_name})
    db.add(audit)
    db.commit()

    return {"message": "Document and associated extracted data deleted successfully."}
