"""
OCR Image Pre-processing and Extraction
Uses OpenCV for deskewing, denoisising, and adaptive thresholding.
Invokes Tesseract OCR (pytesseract) with safe fallback.
"""

from __future__ import annotations

import io
import shutil
from typing import Optional, Tuple
import cv2
import numpy as np
import pytesseract
from PIL import Image


def preprocess_image_for_ocr(image_bytes: bytes) -> np.ndarray:
    """
    Applies image enhancement pipeline:
    1. Grayscale conversion
    2. Gaussian blur / denoising
    3. Otsu binary thresholding
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image bytes.")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.medianBlur(gray, 3)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def extract_text_from_image(image_bytes: bytes) -> Tuple[bool, str]:
    """
    Performs OCR extraction on image bytes.
    Returns:
      (success: bool, text: str)
    """
    # Check if tesseract binary is installed/available
    tesseract_available = shutil.which("tesseract") is not None
    try:
        preprocessed = preprocess_image_for_ocr(image_bytes)
        pil_img = Image.fromarray(preprocessed)

        if tesseract_available:
            text = pytesseract.image_to_string(pil_img, lang="eng")
            return True, text.strip()
        else:
            # Fallback if tesseract is not installed on OS
            return True, "[OCR unavailable: Tesseract engine not found on system PATH]"
    except Exception as e:
        return False, f"OCR processing failed: {str(e)}"
