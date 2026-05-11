"""
Router / Escalation Node.

Makes the final routing decision based on:
- Priority level
- Validation result
- Intent confidence

Decision options:
- reply_directly      → send the draft to the customer
- ask_for_more_info   → request additional details from the customer
- escalate_to_human   → hand off to a human agent
"""

from __future__ import annotations

import logging
import time

from app.core.schemas import (
    DraftResult,
    IntentResult,
    Priority,
    PriorityResult,
    RoutingDecision,
    RoutingResult,
    ValidationResult,
)
from app.core.settings import settings

logger = logging.getLogger(__name__)

# Messages shown to customers for each routing outcome
ESCALATION_MESSAGE = (
    "Thank you for contacting us. Given the nature of your request, "
    "we are connecting you with a specialist who can assist you directly. "
    "Please hold on — a team member will be with you shortly."
)

ASK_MORE_INFO_MESSAGE = (
    "Thank you for reaching out. To assist you better, could you please provide "
    "the following information: {missing_info}? "
    "This will help us resolve your issue as quickly as possible."
)


async def run_router_node(
    intent_result: IntentResult,
    priority_result: PriorityResult,
    validation_result: ValidationResult,
    draft_result: DraftResult,
) -> RoutingResult:
    """Determine the final routing decision and compose the customer-facing response.

    Decision logic (in priority order):
    1. HIGH priority  → escalate_to_human
    2. Low confidence → escalate_to_human
    3. Validation failed → ask_for_more_info (if missing info) or escalate
    4. Default        → reply_directly

    Args:
        intent_result: Output from Intent Node.
        priority_result: Output from Priority Node.
        validation_result: Output from Validation Node.
        draft_result: Output from Draft Node.

    Returns:
        :class:`RoutingResult` with decision, reason, and final response text.
    """
    start = time.perf_counter()

    decision: RoutingDecision
    reason: str
    final_response: str

    # Rule 1: High-risk situations always go to a human
    if priority_result.priority == Priority.HIGH:
        decision = RoutingDecision.ESCALATE_TO_HUMAN
        reason = f"High priority/risk detected: {priority_result.reason}"
        final_response = ESCALATION_MESSAGE

    # Rule 2: Very low intent confidence — agent is not sure what the customer wants
    elif intent_result.confidence < settings.min_intent_confidence:
        decision = RoutingDecision.ESCALATE_TO_HUMAN
        reason = f"Intent confidence too low ({intent_result.confidence:.0%}) to respond reliably"
        final_response = ESCALATION_MESSAGE

    # Rule 3: Validation failed
    elif not validation_result.is_valid:
        if draft_result.missing_information:
            # Ask the customer for specific missing information
            missing_str = ", ".join(draft_result.missing_information)
            decision = RoutingDecision.ASK_FOR_MORE_INFO
            reason = f"Validation issues: {'; '.join(validation_result.validation_issues)}"
            final_response = ASK_MORE_INFO_MESSAGE.format(missing_info=missing_str)
        else:
            # No specific info to ask for — escalate
            decision = RoutingDecision.ESCALATE_TO_HUMAN
            reason = f"Validation failed with no actionable missing info: {validation_result.validation_issues}"
            final_response = ESCALATION_MESSAGE

    # Rule 4: Everything looks good — reply with the draft
    else:
        decision = RoutingDecision.REPLY_DIRECTLY
        reason = f"Validation passed (score={validation_result.validation_score:.0%}), priority={priority_result.priority.value}"
        final_response = draft_result.draft_response

    latency = (time.perf_counter() - start) * 1000
    logger.info(
        "RouterNode: decision=%s reason='%s' latency=%.1fms",
        decision,
        reason,
        latency,
    )

    return RoutingResult(
        decision=decision,
        reason=reason,
        final_response=final_response,
        latency_ms=round(latency, 2),
    )
