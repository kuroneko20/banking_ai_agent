"""
Workflow Orchestrator.

Coordinates all nodes in the correct sequence, collects a workflow trace,
and assembles the final :class:`ChatResponse`.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime

from app.core.schemas import (
    ChatRequest,
    ChatResponse,
    RoutingDecision,
    TraceStep,
    WorkflowState,
)
from app.nodes.draft_node import run_draft_node
from app.nodes.intent_node import run_intent_node
from app.nodes.policy_node import run_policy_node
from app.nodes.priority_node import run_priority_node
from app.nodes.router_node import run_router_node
from app.nodes.validation_node import run_validation_node

logger = logging.getLogger(__name__)


def _trace(step: int, node: str, status: str, latency_ms: float, summary: str) -> TraceStep:
    return TraceStep(step=step, node=node, status=status, latency_ms=latency_ms, summary=summary)


class BankingAgentOrchestrator:
    """Runs the banking AI-agent workflow end-to-end."""

    async def run(self, request: ChatRequest) -> ChatResponse:
        """Execute the full workflow and return a :class:`ChatResponse`.

        Workflow sequence:
        1. Intent Detection
        2. Priority / Risk Assessment
        3. Policy Retrieval
        4. Draft Response Generation
        5. Response Validation
        6. Routing / Escalation Decision

        Args:
            request: Incoming :class:`ChatRequest` from the API layer.

        Returns:
            Complete :class:`ChatResponse` with workflow trace.
        """
        wall_start = time.perf_counter()
        request_id = str(uuid.uuid4())
        session_id = request.session_id
        message = request.message.strip()

        logger.info("Orchestrator START request_id=%s message_len=%d", request_id, len(message))

        state = WorkflowState(
            request_id=request_id,
            session_id=session_id,
            original_message=message,
        )
        trace: list[TraceStep] = []
        step = 0

        # ------------------------------------------------------------------
        # Step 1 — Intent Detection
        # ------------------------------------------------------------------
        step += 1
        try:
            state.intent_result = await run_intent_node(message)
            trace.append(
                _trace(
                    step,
                    "IntentDetectionNode",
                    "success",
                    state.intent_result.latency_ms,
                    f"intent={state.intent_result.intent.value} confidence={state.intent_result.confidence:.0%}",
                )
            )
        except Exception as exc:
            logger.error("Step %d IntentNode failed: %s", step, exc)
            trace.append(_trace(step, "IntentDetectionNode", "error", 0.0, str(exc)))
            return self._error_response(request_id, session_id, message, trace, wall_start)

        # ------------------------------------------------------------------
        # Step 2 — Priority / Risk
        # ------------------------------------------------------------------
        step += 1
        try:
            state.priority_result = await run_priority_node(message, state.intent_result)
            trace.append(
                _trace(
                    step,
                    "PriorityRiskNode",
                    "success",
                    state.priority_result.latency_ms,
                    f"priority={state.priority_result.priority.value} reason={state.priority_result.reason}",
                )
            )
        except Exception as exc:
            logger.error("Step %d PriorityNode failed: %s", step, exc)
            trace.append(_trace(step, "PriorityRiskNode", "error", 0.0, str(exc)))
            return self._error_response(request_id, session_id, message, trace, wall_start)

        # ------------------------------------------------------------------
        # Step 3 — Policy Retrieval
        # ------------------------------------------------------------------
        step += 1
        try:
            state.policy_result = await run_policy_node(state.intent_result)
            trace.append(
                _trace(
                    step,
                    "PolicyRetrievalNode",
                    "success",
                    state.policy_result.latency_ms,
                    f"policy_found={state.policy_result.policy_found} intent={state.policy_result.intent.value}",
                )
            )
        except Exception as exc:
            logger.error("Step %d PolicyNode failed: %s", step, exc)
            trace.append(_trace(step, "PolicyRetrievalNode", "error", 0.0, str(exc)))
            return self._error_response(request_id, session_id, message, trace, wall_start)

        # ------------------------------------------------------------------
        # Step 4 — Draft Response Generation
        # ------------------------------------------------------------------
        step += 1
        try:
            state.draft_result = await run_draft_node(
                message,
                state.intent_result,
                state.priority_result,
                state.policy_result,
            )
            trace.append(
                _trace(
                    step,
                    "DraftResponseNode",
                    "success",
                    state.draft_result.latency_ms,
                    f"model={state.draft_result.model_used} missing={len(state.draft_result.missing_information)} fields",
                )
            )
        except Exception as exc:
            logger.error("Step %d DraftNode failed: %s", step, exc)
            trace.append(_trace(step, "DraftResponseNode", "error", 0.0, str(exc)))
            return self._error_response(request_id, session_id, message, trace, wall_start)

        # ------------------------------------------------------------------
        # Step 5 — Validation
        # ------------------------------------------------------------------
        step += 1
        try:
            state.validation_result = await run_validation_node(
                state.intent_result,
                state.policy_result,
                state.draft_result,
            )
            trace.append(
                _trace(
                    step,
                    "ValidationNode",
                    "success",
                    state.validation_result.latency_ms,
                    f"valid={state.validation_result.is_valid} score={state.validation_result.validation_score:.0%} issues={len(state.validation_result.validation_issues)}",
                )
            )
        except Exception as exc:
            logger.error("Step %d ValidationNode failed: %s", step, exc)
            trace.append(_trace(step, "ValidationNode", "error", 0.0, str(exc)))
            return self._error_response(request_id, session_id, message, trace, wall_start)

        # ------------------------------------------------------------------
        # Step 6 — Routing / Escalation
        # ------------------------------------------------------------------
        step += 1
        try:
            state.routing_result = await run_router_node(
                state.intent_result,
                state.priority_result,
                state.validation_result,
                state.draft_result,
            )
            trace.append(
                _trace(
                    step,
                    "RouterEscalationNode",
                    "success",
                    state.routing_result.latency_ms,
                    f"decision={state.routing_result.decision.value}",
                )
            )
        except Exception as exc:
            logger.error("Step %d RouterNode failed: %s", step, exc)
            trace.append(_trace(step, "RouterEscalationNode", "error", 0.0, str(exc)))
            return self._error_response(request_id, session_id, message, trace, wall_start)

        # ------------------------------------------------------------------
        # Assemble final response
        # ------------------------------------------------------------------
        total_latency = (time.perf_counter() - wall_start) * 1000
        logger.info(
            "Orchestrator END request_id=%s decision=%s total_latency=%.1fms",
            request_id,
            state.routing_result.decision.value,
            total_latency,
        )

        return ChatResponse(
            request_id=request_id,
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat(),
            original_message=message,
            final_response=state.routing_result.final_response,
            routing_decision=state.routing_result.decision,
            intent_result=state.intent_result,
            priority_result=state.priority_result,
            policy_result=state.policy_result,
            draft_result=state.draft_result,
            validation_result=state.validation_result,
            routing_result=state.routing_result,
            workflow_trace=trace,
            total_latency_ms=round(total_latency, 2),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _error_response(
        request_id: str,
        session_id: str | None,
        message: str,
        trace: list[TraceStep],
        wall_start: float,
    ) -> ChatResponse:
        """Return a safe fallback response when a node crashes."""
        from app.core.schemas import (
            DraftResult,
            Intent,
            IntentResult,
            PolicyResult,
            Priority,
            PriorityResult,
            RoutingResult,
            ValidationResult,
        )

        fallback_routing = RoutingResult(
            decision=RoutingDecision.ESCALATE_TO_HUMAN,
            reason="Internal workflow error — escalating for safety",
            final_response=(
                "We apologise for the inconvenience. "
                "We are connecting you with a specialist to assist you."
            ),
            latency_ms=0.0,
        )
        total_latency = (time.perf_counter() - wall_start) * 1000

        return ChatResponse(
            request_id=request_id,
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat(),
            original_message=message,
            final_response=fallback_routing.final_response,
            routing_decision=RoutingDecision.ESCALATE_TO_HUMAN,
            intent_result=IntentResult(intent=Intent.UNKNOWN, confidence=0.0),
            priority_result=PriorityResult(priority=Priority.HIGH, reason="Workflow error"),
            policy_result=PolicyResult(
                intent=Intent.UNKNOWN,
                faq="",
                resolution_guideline="",
                escalation_condition="",
                policy_found=False,
            ),
            draft_result=DraftResult(
                draft_response="",
                suggested_next_action="general_follow_up",
                model_used="none",
            ),
            validation_result=ValidationResult(is_valid=False, validation_score=0.0),
            routing_result=fallback_routing,
            workflow_trace=trace,
            total_latency_ms=round(total_latency, 2),
        )


# Module-level singleton
orchestrator = BankingAgentOrchestrator()
