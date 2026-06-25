"""Tests for the QueueStorm classifier + safety scrubber.

These tests cover the five sample cases from Problem.txt plus a handful
of edge cases (Bengali phishing, mixed-locale messages, etc.).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make `app` importable when running from the backend directory.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.classifier import classify  # noqa: E402
from app.safety import scrub  # noqa: E402

SAMPLE_CASES = [
    pytest.param(
        "I sent 3000 to wrong number this morning, please help",
        "wrong_transfer",
        "high",
        "dispute_resolution",
        False,
        id="sample-1-wrong-transfer",
    ),
    pytest.param(
        "Payment failed but balance deducted",
        "payment_failed",
        "high",
        "payments_ops",
        False,
        id="sample-2-payment-failed",
    ),
    pytest.param(
        "Someone called asking my OTP, is that bKash?",
        "phishing_or_social_engineering",
        "critical",
        "fraud_risk",
        True,
        id="sample-3-phishing",
    ),
    pytest.param(
        "Please refund my last transaction, I changed my mind",
        "refund_request",
        "low",
        "customer_support",
        False,
        id="sample-4-refund",
    ),
    pytest.param(
        "App crashed when I opened it",
        "other",
        "low",
        "customer_support",
        False,
        id="sample-5-other",
    ),
]


@pytest.mark.parametrize(
    "message,expected_case_type,expected_severity,expected_department,expected_review",
    SAMPLE_CASES,
)
def test_sample_case(
    message,
    expected_case_type,
    expected_severity,
    expected_department,
    expected_review,
):
    r = classify(message)
    assert r.case_type == expected_case_type
    assert r.severity == expected_severity
    assert r.department == expected_department
    assert r.human_review_required is expected_review


@pytest.mark.parametrize(
    "message,expected_case_type,expected_severity,expected_department,expected_review",
    SAMPLE_CASES,
)
def test_confidence_for_sample_cases(
    message, expected_case_type, expected_severity, expected_department, expected_review
):
    r = classify(message)
    assert 0.0 <= r.confidence <= 1.0


# -----------------------------------------------------------------------
# Safety rule
# -----------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "Please share your OTP with us to verify.",
        "Send your PIN to confirm the transaction.",
        "Tell us your password so we can unlock your account.",
        "Give me your card number to process the refund.",
        "আপনার পিন দিন যাতে আমরা ভেরিফাই করতে পারি।",
    ],
)
def test_safety_strips_directives(text):
    cleaned = scrub(text)
    lowered = cleaned.lower()
    assert "share your" not in lowered
    assert "send your" not in lowered
    assert "give me your" not in lowered
    assert "tell us your" not in lowered


def test_safety_phishing_summary_is_neutral():
    r = classify("Someone is asking for my OTP and PIN")
    cleaned = scrub(r.agent_summary)
    # The phishing summary must not instruct the customer to share
    # credentials, and it must remain neutral.
    lowered = cleaned.lower()
    for forbidden in [
        "share your otp",
        "share your pin",
        "send your otp",
        "provide your otp",
        "verify your account",
    ]:
        assert forbidden not in lowered, f"forbidden phrase '{forbidden}' in summary: {cleaned!r}"


# -----------------------------------------------------------------------
# Edge cases
# -----------------------------------------------------------------------

def test_bengali_phishing():
    r = classify("একজন আমাকে ফোন করে আমার পিন চাচ্ছে, এটা কি বিকাশ?")
    assert r.case_type == "phishing_or_social_engineering"
    assert r.severity == "critical"
    assert r.human_review_required is True


def test_payment_failed_bengali():
    r = classify("পেমেন্ট ফেইল হয়েছে কিন্তু ব্যালেন্স থেকে টাকা কেটে নিয়েছে")
    assert r.case_type == "payment_failed"
    assert r.severity == "high"


def test_wrong_transfer_below_1000_is_medium():
    r = classify("I sent 200 taka to the wrong number by mistake")
    assert r.case_type == "wrong_transfer"
    assert r.severity == "medium"


def test_wrong_transfer_above_1000_is_high():
    r = classify("I accidentally sent 5000 taka to a wrong number")
    assert r.case_type == "wrong_transfer"
    assert r.severity == "high"


def test_refund_dispute_goes_to_dispute_resolution():
    r = classify("I want a refund, the merchant didn't deliver my order")
    assert r.case_type == "refund_request"
    assert r.severity == "medium"
    assert r.department == "dispute_resolution"


def test_other_fallback_when_no_signal():
    r = classify("Hello, just testing the system.")
    assert r.case_type == "other"
    assert r.severity == "low"
    assert r.department == "customer_support"


def test_confidence_within_range():
    r = classify("Someone called and asked for my OTP")
    assert 0.0 <= r.confidence <= 1.0


@pytest.mark.parametrize(
    "msg",
    [
        "otp requested by phone",
        "PIN asked by caller",
        "password request over sms",
        "someone wants my card number",
    ],
)
def test_agent_summary_never_asks_for_credentials(msg):
    """The auto-fail safety rule across all phishing-flavoured inputs."""
    r = classify(msg)
    cleaned = scrub(r.agent_summary)
    lowered = cleaned.lower()
    for forbidden in [
        "share your otp",
        "share your pin",
        "share your password",
        "send your otp",
        "give us your",
        "provide your otp",
    ]:
        assert forbidden not in lowered, f"forbidden phrase '{forbidden}' in summary: {cleaned!r}"