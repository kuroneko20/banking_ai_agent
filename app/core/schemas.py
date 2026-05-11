"""
Pydantic schemas for all request/response and inter-node data structures.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class Intent(str, Enum):
    TRANSFER_FAILED = "transfer_failed"
    REFUND_REQUEST = "refund_request"
    BLOCKED_ACCOUNT = "blocked_account"
    LOST_CARD = "lost_card"
    CARD_NOT_RECEIVED = "card_not_received"
    SUSPICIOUS_TRANSACTION = "suspicious_transaction"
    ACCOUNT_BALANCE = "account_balance"
    LOAN_SUPPORT = "loan_support"
    PASSWORD_RESET = "password_reset"
    LOGIN_ISSUE = "login_issue"
    GENERAL_INQUIRY = "general_inquiry"
    UNKNOWN = "unknown"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RoutingDecision(str, Enum):
    REPLY_DIRECTLY = "reply_directly"
    ASK_FOR_MORE_INFO = "ask_for_more_info"
    ESCALATE_TO_HUMAN = "escalate_to_human"


# ---------------------------------------------------------------------------
# API Request / Response
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Incoming customer message payload."""

    message: str = Field(..., min_length=1, max_length=2000, description="Customer message")
    session_id: str | None = Field(default=None, description="Optional session identifier")

    model_config = {"json_schema_extra": {"example": {"message": "My account was blocked after a transfer"}}}


class ChatResponse(BaseModel):
    """Full workflow response returned to the caller."""

    request_id: str
    session_id: str | None
    timestamp: str
    original_message: str
    final_response: str
    routing_decision: RoutingDecision
    intent_result: IntentResult
    priority_result: PriorityResult
    policy_result: PolicyResult
    draft_result: DraftResult
    validation_result: ValidationResult
    routing_result: RoutingResult
    workflow_trace: list[TraceStep]
    total_latency_ms: float


# ---------------------------------------------------------------------------
# Node result schemas
# ---------------------------------------------------------------------------


class IntentResult(BaseModel):
    """Output of Intent Detection Node."""

    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    extracted_entities: dict[str, Any] = Field(default_factory=dict)
    raw_scores: dict[str, float] = Field(default_factory=dict)
    latency_ms: float = 0.0


class PriorityResult(BaseModel):
    """Output of Priority/Risk Node."""

    priority: Priority
    reason: str
    risk_factors: list[str] = Field(default_factory=list)
    latency_ms: float = 0.0


class PolicyResult(BaseModel):
    """Output of Policy Retrieval Node."""

    intent: Intent
    faq: str
    resolution_guideline: str
    escalation_condition: str
    policy_found: bool
    latency_ms: float = 0.0


class DraftResult(BaseModel):
    """Output of Draft Response Node."""

    draft_response: str
    missing_information: list[str] = Field(default_factory=list)
    suggested_next_action: str
    model_used: str
    latency_ms: float = 0.0


class ValidationResult(BaseModel):
    """Output of Validation Node."""

    is_valid: bool
    validation_score: float = Field(ge=0.0, le=1.0)
    validation_issues: list[str] = Field(default_factory=list)
    latency_ms: float = 0.0


class RoutingResult(BaseModel):
    """Output of Router Node."""

    decision: RoutingDecision
    reason: str
    final_response: str
    latency_ms: float = 0.0


# ---------------------------------------------------------------------------
# Workflow trace
# ---------------------------------------------------------------------------


class TraceStep(BaseModel):
    """Single step in the workflow trace."""

    step: int
    node: str
    status: str  # "success" | "error" | "skipped"
    latency_ms: float
    summary: str


# ---------------------------------------------------------------------------
# Internal aggregated state passed between nodes
# ---------------------------------------------------------------------------


class WorkflowState(BaseModel):
    """Mutable state object carried through the entire workflow."""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    original_message: str = ""
    intent_result: IntentResult | None = None
    priority_result: PriorityResult | None = None
    policy_result: PolicyResult | None = None
    draft_result: DraftResult | None = None
    validation_result: ValidationResult | None = None
    routing_result: RoutingResult | None = None
    workflow_trace: list[TraceStep] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
