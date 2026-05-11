"""
Draft Response Node.

Calls the Ollama LLM to generate a customer-facing response draft
using the detected intent, priority, and retrieved policy as context.
"""

from __future__ import annotations

import json
import logging
import time

from app.clients.ollama_client import ollama_client
from app.core.schemas import DraftResult, IntentResult, PolicyResult, Priority, PriorityResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — sets the assistant's persona and output format
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a professional banking customer support specialist.
Your role is to provide accurate, empathetic, and helpful responses to customers.

GUIDELINES:
- Always be polite, clear, and concise.
- Reference the policy information provided to give accurate guidance.
- If information is missing, ask for it politely.
- For high-priority or fraud-related issues, express urgency and empathy.
- Never promise outcomes you cannot guarantee.
- Do not share internal system notes or policy references directly.
- Keep the response focused and professional — 2-4 short paragraphs max.

OUTPUT FORMAT (respond with valid JSON only, no markdown):
{
  "draft_response": "<customer-facing response text>",
  "missing_information": ["<info item 1>", "<info item 2>"],
  "suggested_next_action": "<one of: provide_transaction_id | verify_identity | contact_fraud_team | wait_for_processing | visit_branch | reset_password | general_follow_up>"
}"""

# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


def _build_prompt(
    message: str,
    intent_result: IntentResult,
    priority_result: PriorityResult,
    policy_result: PolicyResult,
) -> str:
    return f"""CUSTOMER MESSAGE:
{message}

DETECTED INTENT: {intent_result.intent.value} (confidence: {intent_result.confidence:.0%})
PRIORITY / RISK: {priority_result.priority.value.upper()} — {priority_result.reason}

RELEVANT POLICY:
FAQ: {policy_result.faq}

RESOLUTION GUIDELINE:
{policy_result.resolution_guideline}

ESCALATION CONDITION:
{policy_result.escalation_condition}

Generate a professional customer support response following the OUTPUT FORMAT specified.
Remember: respond ONLY with valid JSON."""


# ---------------------------------------------------------------------------
# Fallback draft when LLM is unavailable
# ---------------------------------------------------------------------------


def _fallback_draft(priority: Priority, intent_str: str) -> DraftResult:
    """Generate a safe fallback response when Ollama is unreachable."""
    if priority == Priority.HIGH:
        text = (
            "Thank you for contacting us. We understand this is an urgent matter. "
            "Please be assured our team is prioritising your case. "
            "For immediate assistance, please call our 24/7 hotline."
        )
    else:
        text = (
            "Thank you for reaching out to us. "
            "We have received your enquiry and will get back to you as soon as possible. "
            "Please have your account details ready for reference."
        )
    return DraftResult(
        draft_response=text,
        missing_information=["account_number", "transaction_reference"],
        suggested_next_action="general_follow_up",
        model_used="fallback",
        latency_ms=0.0,
    )


# ---------------------------------------------------------------------------
# Node runner
# ---------------------------------------------------------------------------


async def run_draft_node(
    message: str,
    intent_result: IntentResult,
    priority_result: PriorityResult,
    policy_result: PolicyResult,
) -> DraftResult:
    """Call Ollama to generate a draft customer response.

    Args:
        message: Original customer message.
        intent_result: Output from Intent Node.
        priority_result: Output from Priority Node.
        policy_result: Output from Policy Node.

    Returns:
        :class:`DraftResult` with draft text, missing info, and next action.
    """
    start = time.perf_counter()
    prompt = _build_prompt(message, intent_result, priority_result, policy_result)

    try:
        raw = await ollama_client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=800,
        )

        # Strip any accidental markdown fences
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed: dict = json.loads(clean)

        latency = (time.perf_counter() - start) * 1000
        logger.info("DraftNode: response generated latency=%.1fms", latency)

        return DraftResult(
            draft_response=parsed.get("draft_response", ""),
            missing_information=parsed.get("missing_information", []),
            suggested_next_action=parsed.get("suggested_next_action", "general_follow_up"),
            model_used=ollama_client.model,
            latency_ms=round(latency, 2),
        )

    except json.JSONDecodeError as exc:
        logger.warning("DraftNode: JSON parse failed, using raw text. %s", exc)
        latency = (time.perf_counter() - start) * 1000
        # Return the raw LLM text as draft even if JSON parsing failed
        return DraftResult(
            draft_response=raw if "raw" in dir() else "We are processing your request.",
            missing_information=[],
            suggested_next_action="general_follow_up",
            model_used=ollama_client.model,
            latency_ms=round(latency, 2),
        )

    except RuntimeError as exc:
        logger.error("DraftNode: Ollama unavailable (%s), using fallback.", exc)
        result = _fallback_draft(priority_result.priority, intent_result.intent.value)
        result.latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return result
