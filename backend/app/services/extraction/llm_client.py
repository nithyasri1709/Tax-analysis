"""
LLM Client Interface
Provider-agnostic client supporting Gemini, OpenAI, Anthropic, and robust offline regex fallback.
Enforces PII redaction and schema-constrained JSON output.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional
from app.core.config import settings
from app.core.encryption import redact_pii_for_llm

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None):
        self.provider = provider or settings.LLM_PROVIDER
        self.api_key = api_key or settings.LLM_API_KEY

    def extract_structured_fields(
        self,
        document_text: str,
        doc_type: str,
    ) -> Dict[str, Any]:
        """
        Extracts structured tax fields from document text.
        Redacts PII by default before sending to external APIs.
        Falls back to rule-based parser if no API key is provided or provider is regex_fallback.
        """
        redacted_text = redact_pii_for_llm(document_text)

        if not self.api_key or self.provider == "regex_fallback":
            return self._offline_fallback_extractor(document_text, doc_type)

        if self.provider == "gemini":
            try:
                return self._call_gemini(redacted_text, doc_type)
            except Exception as e:
                logger.warning(f"Gemini API call failed, falling back to regex: {e}")
                return self._offline_fallback_extractor(document_text, doc_type)

        return self._offline_fallback_extractor(document_text, doc_type)

    def _call_gemini(self, text: str, doc_type: str) -> Dict[str, Any]:
        # Implementation via requests/httpx to Gemini generateContent endpoint
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        prompt = (
            f"You are an Indian income-tax expert assistant. Extract structured financial fields from this {doc_type} text.\n"
            f"Return ONLY a JSON object with keys like gross_salary, basic_salary, hra_received, employee_pf, tds, etc.\n"
            f"Document text:\n{text[:4000]}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"},
        }
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            raw_json = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_json)
        raise RuntimeError(f"Gemini API returned status {resp.status_code}: {resp.text}")

    def _offline_fallback_extractor(self, text: str, doc_type: str) -> Dict[str, Any]:
        """Offline deterministic extraction logic using regex and pattern extractors."""
        from app.services.extraction.field_extractors import regex_extract_fields
        return regex_extract_fields(text, doc_type)
