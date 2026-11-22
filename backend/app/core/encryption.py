"""
Data Encryption & PII Masking Utilities
Provides symmetric encryption (Fernet / AES-128-CBC with HMAC-SHA256) for PII and documents at rest.
"""

import base64
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY.encode("utf-8")
    # Ensure key is valid 32-byte base64 URL safe
    try:
        return Fernet(key)
    except Exception:
        # Fallback to generating a deterministic 32-byte base64 key
        raw = key.ljust(32, b"0")[:32]
        b64_key = base64.urlsafe_b64encode(raw)
        return Fernet(b64_key)


def encrypt_text(text: str) -> str:
    """Encrypts plaintext string to URL-safe base64 encrypted string."""
    if not text:
        return ""
    f = _get_fernet()
    return f.encrypt(text.encode("utf-8")).decode("utf-8")


def decrypt_text(ciphertext: str) -> str:
    """Decrypts ciphertext string to plaintext string."""
    if not ciphertext:
        return ""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")


def encrypt_bytes(data: bytes) -> bytes:
    """Encrypts raw byte buffer (e.g. document contents)."""
    f = _get_fernet()
    return f.encrypt(data)


def decrypt_bytes(encrypted_data: bytes) -> bytes:
    """Decrypts encrypted raw byte buffer."""
    f = _get_fernet()
    return f.decrypt(encrypted_data)


def mask_pan(pan: str) -> str:
    """
    Masks Indian PAN (Permanent Account Number).
    Standard format: 5 letters, 4 digits, 1 letter (e.g. ABCDE1234F).
    Masked: ABCDE****F
    """
    if not pan:
        return ""
    clean = pan.strip().upper()
    if len(clean) == 10:
        return f"{clean[:5]}****{clean[-1]}"
    if len(clean) > 4:
        return f"{clean[:2]}****{clean[-2:]}"
    return "****"


def redact_pii_for_llm(text: str) -> str:
    """Redacts PAN, Aadhaar, and bank account numbers before feeding to external LLMs."""
    import re
    # PAN pattern: 5 letters + 4 digits + 1 letter
    pan_pattern = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)
    # Aadhaar pattern: 12 digits
    aadhaar_pattern = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
    # Bank account pattern: 9 to 18 continuous digits
    account_pattern = re.compile(r"\b\d{9,18}\b")

    res = pan_pattern.sub("[REDACTED_PAN]", text)
    res = aadhaar_pattern.sub("[REDACTED_AADHAAR]", res)
    res = account_pattern.sub("[REDACTED_ACCOUNT]", res)
    return res
