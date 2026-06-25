"""Pydantic request/response models for the QueueStorm Warmup API."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Channel = Literal["app", "sms", "call_center", "merchant_portal"]
Locale = Literal["bn", "en", "mixed"]

CaseType = Literal[
    "wrong_transfer",
    "payment_failed",
    "refund_request",
    "phishing_or_social_engineering",
    "other",
]

Severity = Literal["low", "medium", "high", "critical"]

Department = Literal[
    "customer_support",
    "dispute_resolution",
    "payments_ops",
    "fraud_risk",
]


class SortTicketRequest(BaseModel):
    """Incoming CRM ticket payload."""

    ticket_id: str = Field(..., min_length=1, description="Echoed back in the response.")
    channel: Optional[Channel] = Field(
        default=None, description="Originating channel of the ticket."
    )
    locale: Optional[Locale] = Field(
        default=None, description="Locale of the customer message."
    )
    message: str = Field(..., min_length=1, description="Free-text customer complaint.")


class SortTicketResponse(BaseModel):
    """Structured classification the agent dashboard consumes."""

    ticket_id: str
    case_type: CaseType
    severity: Severity
    department: Department
    agent_summary: str
    human_review_required: bool
    confidence: float = Field(..., ge=0.0, le=1.0)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str