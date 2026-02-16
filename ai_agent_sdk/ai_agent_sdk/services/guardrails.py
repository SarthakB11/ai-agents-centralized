"""
Guardrails Service — PII detection, prompt injection, output safety.
"""

import re
import logging
from typing import Dict

logger = logging.getLogger(__name__)

PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "aadhaar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "pan": r"\b[A-Z]{5}\d{4}[A-Z]\b",
}

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+the\s+above", r"disregard\s+(all\s+)?previous",
    r"forget\s+(all\s+)?(your\s+)?instructions",
    r"you\s+are\s+now\s+a", r"act\s+as\s+if",
    r"pretend\s+(you\s+are|to\s+be)",
    r"override\s+(your\s+)?(system|safety)",
    r"jailbreak", r"DAN\s+mode", r"\[system\]", r"<\|system\|>",
]


class Guardrails:
    def __init__(self, pii_filter: bool = True, injection_detection: bool = True):
        self.pii_filter = pii_filter
        self.injection_detection = injection_detection

    def check_input(self, text: str) -> Dict:
        warnings = []
        sanitized = text
        if self.injection_detection:
            inj = self.detect_injection(text)
            if inj["detected"]:
                return {"is_safe": False, "warnings": [f"Injection: {inj['pattern']}"],
                        "sanitized_text": text, "blocked": True, "reason": "prompt_injection"}
        if self.pii_filter:
            pii = self.detect_pii(text)
            if pii["found"]:
                warnings.extend([f"PII: {t}" for t in pii["types"]])
                sanitized = self.redact_pii(text)
        return {"is_safe": True, "warnings": warnings, "sanitized_text": sanitized, "blocked": False}

    def check_output(self, text: str, confidence: float = 1.0, min_confidence: float = 0.5) -> Dict:
        warnings = []
        sanitized = text
        if confidence < min_confidence:
            warnings.append(f"Low confidence: {confidence:.2f}")
        if self.pii_filter:
            pii = self.detect_pii(text)
            if pii["found"]:
                warnings.extend([f"PII in output: {t}" for t in pii["types"]])
                sanitized = self.redact_pii(text)
        return {"is_safe": len(warnings) == 0, "warnings": warnings, "sanitized_text": sanitized}

    def detect_pii(self, text: str) -> Dict:
        found = [t for t, p in PII_PATTERNS.items() if re.search(p, text)]
        return {"found": len(found) > 0, "types": found}

    def redact_pii(self, text: str) -> str:
        r = text
        for t, p in PII_PATTERNS.items():
            r = re.sub(p, f"[REDACTED_{t.upper()}]", r)
        return r

    def detect_injection(self, text: str) -> Dict:
        tl = text.lower()
        for p in INJECTION_PATTERNS:
            if re.search(p, tl):
                return {"detected": True, "pattern": p}
        return {"detected": False, "pattern": None}

    def enforce_token_limit(self, text: str, max_chars: int = 10000) -> str:
        if len(text) > max_chars:
            return text[:max_chars] + "\n[TRUNCATED]"
        return text
