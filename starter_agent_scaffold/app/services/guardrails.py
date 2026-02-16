"""
Guardrails Service — Input/output safety filters.

Conforms to the Risk & Compliance Blueprint:
- PII detection and redaction
- Prompt injection detection
- Output confidence thresholding
- Token limit enforcement
"""

import re
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


# --- PII Patterns ---

PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "aadhaar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",  # Indian Aadhaar
    "pan": r"\b[A-Z]{5}\d{4}[A-Z]\b",  # Indian PAN
}

# --- Prompt Injection Patterns ---

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+the\s+above",
    r"disregard\s+(all\s+)?previous",
    r"forget\s+(all\s+)?(your\s+)?instructions",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+if",
    r"pretend\s+(you\s+are|to\s+be)",
    r"override\s+(your\s+)?(system|safety)",
    r"jailbreak",
    r"DAN\s+mode",
    r"\[system\]",
    r"<\|system\|>",
]


class Guardrails:
    """
    Safety layer for agent inputs and outputs.
    """

    def __init__(self, pii_filter: bool = True, injection_detection: bool = True):
        self.pii_filter = pii_filter
        self.injection_detection = injection_detection

    def check_input(self, text: str) -> Dict:
        """
        Run all input checks. Returns a safety report.

        Returns:
            dict with: is_safe, warnings, sanitized_text
        """
        warnings = []
        sanitized = text

        # Check for prompt injection
        if self.injection_detection:
            injection_result = self.detect_injection(text)
            if injection_result["detected"]:
                warnings.append(f"⚠️  Prompt injection attempt detected: {injection_result['pattern']}")
                return {
                    "is_safe": False,
                    "warnings": warnings,
                    "sanitized_text": text,
                    "blocked": True,
                    "reason": "prompt_injection",
                }

        # Detect and redact PII
        if self.pii_filter:
            pii_result = self.detect_pii(text)
            if pii_result["found"]:
                warnings.extend([f"PII detected: {t}" for t in pii_result["types"]])
                sanitized = self.redact_pii(text)

        return {
            "is_safe": True,
            "warnings": warnings,
            "sanitized_text": sanitized,
            "blocked": False,
        }

    def check_output(self, text: str, confidence: float = 1.0, min_confidence: float = 0.5) -> Dict:
        """
        Run output safety checks.

        Returns:
            dict with: is_safe, warnings, sanitized_text
        """
        warnings = []
        sanitized = text

        # Confidence check
        if confidence < min_confidence:
            warnings.append(f"Low confidence: {confidence:.2f} (threshold: {min_confidence})")

        # Redact PII from output
        if self.pii_filter:
            pii_result = self.detect_pii(text)
            if pii_result["found"]:
                warnings.extend([f"PII in output: {t}" for t in pii_result["types"]])
                sanitized = self.redact_pii(text)

        return {
            "is_safe": len(warnings) == 0,
            "warnings": warnings,
            "sanitized_text": sanitized,
        }

    def detect_pii(self, text: str) -> Dict:
        """Detect PII in text."""
        found_types = []
        for pii_type, pattern in PII_PATTERNS.items():
            if re.search(pattern, text):
                found_types.append(pii_type)

        return {"found": len(found_types) > 0, "types": found_types}

    def redact_pii(self, text: str) -> str:
        """Redact PII from text with [REDACTED] markers."""
        redacted = text
        for pii_type, pattern in PII_PATTERNS.items():
            redacted = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", redacted)
        return redacted

    def detect_injection(self, text: str) -> Dict:
        """Detect prompt injection attempts."""
        text_lower = text.lower()
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                return {"detected": True, "pattern": pattern}
        return {"detected": False, "pattern": None}

    def enforce_token_limit(self, text: str, max_chars: int = 10000) -> str:
        """Truncate input to prevent token explosion attacks."""
        if len(text) > max_chars:
            logger.warning(f"Input truncated from {len(text)} to {max_chars} chars")
            return text[:max_chars] + "\n[TRUNCATED]"
        return text
