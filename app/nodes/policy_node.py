"""
Policy Retrieval Node.

Looks up the policy / FAQ record that matches the detected intent
and returns it as a structured :class:`PolicyResult`.
"""

from __future__ import annotations

import logging
import time

from app.core.schemas import Intent, IntentResult, PolicyResult
from app.data.policies import get_policy

logger = logging.getLogger(__name__)


async def run_policy_node(intent_result: IntentResult) -> PolicyResult:
    """Retrieve the banking policy for the detected intent.

    Args:
        intent_result: Output from the Intent Detection Node.

    Returns:
        :class:`PolicyResult` with FAQ text, resolution steps, and escalation conditions.
    """
    start = time.perf_counter()

    intent = intent_result.intent
    policy = get_policy(intent)
    policy_found = intent != Intent.UNKNOWN

    latency = (time.perf_counter() - start) * 1000
    logger.info(
        "PolicyNode: intent=%s policy_found=%s latency=%.1fms",
        intent,
        policy_found,
        latency,
    )

    return PolicyResult(
        intent=intent,
        faq=policy["faq"],
        resolution_guideline=policy["resolution_guideline"],
        escalation_condition=policy["escalation_condition"],
        policy_found=policy_found,
        latency_ms=round(latency, 2),
    )
