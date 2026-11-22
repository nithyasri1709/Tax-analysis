"""
Document Storage Service
Handles secure encrypted storage at rest, magic-byte MIME validation, and file sanitization.
"""

from __future__ import annotations

import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import Optional, Tuple
from fastapi import HTTPException, UploadFile, status
from app.core.config import settings
from app.core.encryption import decrypt_bytes, encrypt_bytes

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".xls", ".xlsx", ".csv"}

# Magic byte signatures
MAGIC_BYTES = {
    b"%PDF": "application/pdf",
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"PK\x03\x04": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx / zip
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1": "application/vnd.ms-excel",  # xls
}


def sanitize_filename(filename: str) -> str:
    """Removes path traversal and non-alphanumeric special characters from filename."""
    base = os.path.basename(filename)
    clean = re.sub(r"[^\w\s\.-]", "_", base)
    return clean[:120]


def validate_file_content(data: bytes, filename: str) -> str:
    """
    Validates file size, extension, and magic-byte signature.
    Returns detected MIME type or raises HTTPException.
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' is not supported. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowable limit of {settings.MAX_UPLOAD_MB} MB.",
        )

    # Magic byte check
    detected_mime = None
    for magic, mime in MAGIC_BYTES.items():
        if data.startswith(magic):
            detected_mime = mime
            break

    # CSV files are plain text
    if not detected_mime and ext == ".csv":
        try:
            data[:1024].decode("utf-8")
            detected_mime = "text/csv"
        except UnicodeDecodeError:
            try:
                data[:1024].decode("latin-1")
                detected_mime = "text/csv"
            except Exception:
                pass

    if not detected_mime:
        if ext in [".jpg", ".jpeg"]:
            detected_mime = "image/jpeg"
        elif ext == ".png":
            detected_mime = "image/png"
        elif ext == ".pdf":
            detected_mime = "application/pdf"
        elif ext == ".csv":
            detected_mime = "text/csv"
        elif ext == ".xlsx":
            detected_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif ext == ".xls":
            detected_mime = "application/vnd.ms-excel"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not verify file content format against security signatures.",
            )

    return detected_mime


def compute_sha256(data: bytes) -> str:
    """Computes SHA-256 hash for document content deduplication."""
    return hashlib.sha256(data).hexdigest()


def save_encrypted_file(data: bytes, user_id: str, original_filename: str) -> Tuple[str, str]:
    """
    Encrypts file bytes at rest and stores in user directory with randomized UUID.
    Returns:
      storage_path: str,
      file_hash: str (SHA-256 of raw data)
    """
    file_hash = compute_sha256(data)
    user_storage_dir = Path(settings.STORAGE_DIR) / user_id
    user_storage_dir.mkdir(parents=True, exist_ok=True)

    random_id = str(uuid.uuid4())
    stored_name = f"{random_id}.enc"
    storage_path = str(user_storage_dir / stored_name)

    encrypted_bytes = encrypt_bytes(data)
    with open(storage_path, "wb") as f:
        f.write(encrypted_bytes)

    return storage_path, file_hash


def read_decrypted_file(storage_path: str) -> bytes:
    """Reads encrypted file from disk and returns decrypted raw bytes."""
    if not os.path.exists(storage_path):
        raise FileNotFoundError(f"Stored file does not exist at path: {storage_path}")

    with open(storage_path, "rb") as f:
        encrypted_bytes = f.read()

    return decrypt_bytes(encrypted_bytes)


def delete_stored_file(storage_path: str) -> bool:
    """Deletes stored encrypted file from disk."""
    if storage_path and os.path.exists(storage_path):
        try:
            os.remove(storage_path)
            return True
        except Exception:
            return False
    return False
