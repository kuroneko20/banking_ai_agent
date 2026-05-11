"""
Priority / Risk Assessment Node.

Evaluates the urgency and risk of the incoming request based on:
- Detected intent
- Intent confidence
- Keywords in the customer message
"""

from __future__ import annotations

import logging
import time

from app.core.schemas import Intent, IntentResult, Priority, PriorityResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Priority rule tables
# ---------------------------------------------------------------------------

HIGH_PRIORITY_INTENTS: set[Intent] = {
    Intent.SUSPICIOUS_TRANSACTION,
    Intent.BLOCKED_ACCOUNT,
    Intent.LOST_CARD,
}

MEDIUM_PRIORITY_INTENTS: set[Intent] = {
    Intent.TRANSFER_FAILED,
    Intent.REFUND_REQUEST,
    Intent.CARD_NOT_RECEIVED,
    Intent.LOGIN_ISSUE,
}

LOW_PRIORITY_INTENTS: set[Intent] = {
    Intent.ACCOUNT_BALANCE,
    Intent.LOAN_SUPPORT,
    Intent.PASSWORD_RESET,
    Intent.GENERAL_INQUIRY,
    Intent.UNKNOWN,
}

# Additional HIGH-risk keywords that upgrade any intent to HIGH
HIGH_RISK_KEYWORDS: list[str] = [
    "fraud",
    "hack",
    "hacked",
    "stolen",
    "unauthorized",
    "lost all my money",
    "emergency",
    "police",
    "scam",
    "phishing",
    "identity theft",
]

# Keywords that escalate LOW to MEDIUM
MEDIUM_RISK_KEYWORDS: list[str] = [
    "urgent",
    "asap",
    "immediately",
    "still pending",
    "days ago",
    "week ago",
    "not resolved",
]


def _detect_risk_factors(message: str) -> list[str]:
    """Return a list of risk signal strings found in *message*."""
    lower = message.lower()
    factors: list[str] = []

    for kw in HIGH_RISK_KEYWORDS:
        if kw in lower:
            factors.append(f"HIGH keyword: '{kw}'")

    for kw in MEDIUM_RISK_KEYWORDS:
        if kw in lower:
            factors.append(f"MEDIUM keyword: '{kw}'")

    return factors


async def run_priority_node(message: str, intent_result: IntentResult) -> PriorityResult:
    """Classify the risk/priority of the customer's request.

    Args:
        message: The original customer message.
        intent_result: Output from the IntentNode.

    Returns:
        A :class:`PriorityResult` with priority level and reason.
    """
    start = time.perf_counter()

    intent = intent_result.intent
    risk_factors = _detect_risk_factors(message)
    has_high_keyword = any("HIGH" in f for f in risk_factors)

    # Determine base priority from intent
    if intent in HIGH_PRIORITY_INTENTS or has_high_keyword:
        priority = Priority.HIGH
        reason = (
            f"Intent '{intent.value}' is inherently high-risk"
            if not has_high_keyword
            else "High-risk keywords detected in message"
        )
    elif intent in MEDIUM_PRIORITY_INTENTS:
        priority = Priority.MEDIUM
        reason = f"Intent '{intent.value}' requires timely attention"
    else:
        priority = Priority.LOW
        reason = f"Intent '{intent.value}' is a standard inquiry"

    # Upgrade LOW → MEDIUM if medium risk keywords found
    has_medium_keyword = any("MEDIUM" in f for f in risk_factors)
    if priority == Priority.LOW and has_medium_keyword:
        priority = Priority.MEDIUM
        reason += " (urgency keywords detected)"

    latency = (time.perf_counter() - start) * 1000
    logger.info(
        "PriorityNode: priority=%s reason='%s' latency=%.1fms",
        priority,
        reason,
        latency,
    )

    return PriorityResult(
        priority=priority,
        reason=reason,
        risk_factors=risk_factors,
        latency_ms=round(latency, 2),
    )
