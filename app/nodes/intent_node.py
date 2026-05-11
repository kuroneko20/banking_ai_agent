"""
Intent Detection Node.

Uses keyword/rule-based scoring as the primary classifier,
then optionally refines with an LLM if confidence is low.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.core.schemas import Intent, IntentResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keyword rules: intent → (keywords, weight)
# The weight is used to scale the score contribution of each match.
# ---------------------------------------------------------------------------

INTENT_RULES: dict[Intent, list[tuple[list[str], float]]] = {
    Intent.TRANSFER_FAILED: [
        (["transfer", "sent", "wire", "remit"], 0.4),
        (["failed", "not received", "didn't arrive", "missing", "stuck", "pending"], 0.6),
    ],
    Intent.REFUND_REQUEST: [
        (["refund", "money back", "return payment", "reimburs", "chargeback"], 1.0),
    ],
    Intent.BLOCKED_ACCOUNT: [
        (["blocked", "locked", "frozen", "suspended", "restrict"], 0.7),
        (["account", "profile", "access"], 0.3),
    ],
    Intent.LOST_CARD: [
        (["lost", "stolen", "missing card", "can't find my card"], 0.7),
        (["card", "debit", "credit"], 0.3),
    ],
    Intent.CARD_NOT_RECEIVED: [
        (["not received", "haven't received", "not arrived", "delivery"], 0.6),
        (["card", "new card", "replacement card"], 0.4),
    ],
    Intent.SUSPICIOUS_TRANSACTION: [
        (["suspicious", "fraud", "unauthorized", "didn't make", "strange", "unknown charge", "hacked"], 1.0),
        (["transaction", "charge", "payment", "purchase"], 0.3),
    ],
    Intent.ACCOUNT_BALANCE: [
        (["balance", "how much", "statement", "funds available", "check my account"], 1.0),
    ],
    Intent.LOAN_SUPPORT: [
        (["loan", "borrow", "mortgage", "credit line", "lending", "finance"], 1.0),
    ],
    Intent.PASSWORD_RESET: [
        (["password", "reset", "forgot", "change password", "update password"], 1.0),
    ],
    Intent.LOGIN_ISSUE: [
        (["login", "log in", "sign in", "can't access", "unable to log", "authentication"], 0.8),
        (["error", "failed", "denied"], 0.2),
    ],
    Intent.GENERAL_INQUIRY: [
        (["hours", "branch", "contact", "phone number", "email", "website", "service", "product"], 0.5),
    ],
}

# Entities to extract (pattern → key name)
ENTITY_PATTERNS: dict[str, list[str]] = {
    "amount": ["$", "usd", "dollar", "amount", "total"],
    "card_type": ["debit card", "credit card", "visa", "mastercard"],
    "transaction_ref": ["ref", "reference", "txn", "transaction id"],
}


def _score_intent(message: str) -> dict[str, float]:
    """Return a score for each intent based on keyword matching."""
    lower = message.lower()
    scores: dict[str, float] = {intent.value: 0.0 for intent in Intent}

    for intent, rule_groups in INTENT_RULES.items():
        total = 0.0
        for keywords, weight in rule_groups:
            if any(kw in lower for kw in keywords):
                total += weight
        scores[intent.value] = min(total, 1.0)

    return scores


def _extract_entities(message: str) -> dict[str, Any]:
    """Extract simple named entities from the message."""
    lower = message.lower()
    entities: dict[str, Any] = {}
    for entity_key, patterns in ENTITY_PATTERNS.items():
        if any(p in lower for p in patterns):
            entities[entity_key] = True  # flag — actual extraction needs NLP
    return entities


async def run_intent_node(message: str) -> IntentResult:
    """Detect the banking intent in *message*.

    Returns an :class:`IntentResult` with intent, confidence, and entities.
    """
    start = time.perf_counter()

    scores = _score_intent(message)
    best_intent_key = max(scores, key=lambda k: scores[k])
    best_score = scores[best_intent_key]

    # If no rule produced a signal, classify as UNKNOWN
    if best_score < 0.1:
        detected = Intent.UNKNOWN
        confidence = 0.1
    else:
        detected = Intent(best_intent_key)
        confidence = min(best_score, 1.0)

    entities = _extract_entities(message)
    latency = (time.perf_counter() - start) * 1000

    logger.info(
        "IntentNode: intent=%s confidence=%.2f latency=%.1fms",
        detected,
        confidence,
        latency,
    )

    return IntentResult(
        intent=detected,
        confidence=confidence,
        extracted_entities=entities,
        raw_scores={k: round(v, 3) for k, v in scores.items() if v > 0},
        latency_ms=round(latency, 2),
    )
