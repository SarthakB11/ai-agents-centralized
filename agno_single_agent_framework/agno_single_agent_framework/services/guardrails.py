"""
Guardrails — PII detection and prompt injection protection
via Agno's native guardrail system.

Guardrails attach to the Agent as pre_hooks / post_hooks, so Agno
enforces them automatically on every run — no manual checking needed.

Built-in guardrails (from agno.guardrails):
  - PromptInjectionGuardrail  — blocks jailbreak / injection attempts
  - PIIDetectionGuardrail     — masks or blocks PII (emails, SSNs, credit cards, phones)
  - OpenAIModerationGuardrail — content-policy check via OpenAI moderation API

Custom guardrails: subclass BaseGuardrail and implement check() / async_check().

Usage:
    from agno_single_agent_framework.services.guardrails import build_guardrail_hooks
    pre_hooks, post_hooks = build_guardrail_hooks()
    agent = Agent(..., pre_hooks=pre_hooks, post_hooks=post_hooks)

Errors raised by guardrails:
    from agno.exceptions import InputCheckError, OutputCheckError
"""

import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

try:
    from agno.guardrails import PIIDetectionGuardrail, PromptInjectionGuardrail
    _GUARDRAILS_AVAILABLE = True
except ImportError:
    _GUARDRAILS_AVAILABLE = False
    logger.warning(
        "agno.guardrails not available — guardrails will be disabled. "
        "Ensure you have a recent version of agno installed."
    )


def build_guardrail_hooks(
    pii_filter: bool = True,
    injection_detection: bool = True,
    mask_pii: bool = True,
) -> Tuple[List, List]:
    """
    Build pre_hooks and post_hooks lists for Agno's Agent.

    Args:
        pii_filter: Detect PII (emails, SSNs, credit cards, phone numbers).
        injection_detection: Detect prompt injection and jailbreak attempts.
        mask_pii: Mask PII with asterisks rather than blocking the request.
                  Defaults to True to preserve original behavior (redact, don't block).

    Returns:
        (pre_hooks, post_hooks) tuples — pass directly to Agent():
            Agent(..., pre_hooks=pre_hooks, post_hooks=post_hooks)
    """
    pre_hooks: List = []
    post_hooks: List = []

    if not _GUARDRAILS_AVAILABLE:
        return pre_hooks, post_hooks

    if injection_detection:
        pre_hooks.append(PromptInjectionGuardrail())
        logger.debug("Guardrail: PromptInjectionGuardrail added to pre_hooks")

    if pii_filter:
        pre_hooks.append(PIIDetectionGuardrail(mask_pii=mask_pii))
        post_hooks.append(PIIDetectionGuardrail(mask_pii=mask_pii))
        logger.debug("Guardrail: PIIDetectionGuardrail added to pre_hooks + post_hooks (mask_pii=%s)", mask_pii)

    return pre_hooks, post_hooks
