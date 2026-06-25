"""Rules-based classification engine.

Pipeline:
    1. Normalise the message.
    2. Score every case_type using pattern weights.
    3. Pick the highest scorer; tie-break by fixed priority.
    4. Derive severity and department from the case_type plus cues.
    5. Build a one-or-two-sentence summary.
    6. Compute confidence from match strength.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .safety import CREDENTIAL_TERMS
from .schemas import CaseType, Department, Severity

# Each entry: (compiled regex, weight). Weights are tuned for the
# five sample cases in Problem.txt.

_PHISHING_PATTERNS: List[Tuple[re.Pattern[str], float]] = [
    # Reuse the safety module's credential vocabulary so the two
    # lists stay in sync.
    *(
        (re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE), 0.9)
        for term in CREDENTIAL_TERMS
    ),
    (re.compile(r"\bshare\s+(?:your|the)\b", re.I), 0.8),
    (re.compile(r"\bsend\s+(?:your|the)\s+(?:code|otp|pin|password)\b", re.I), 0.9),
    (re.compile(r"\bgive\s+(?:me|us)\s+(?:your|the)\b", re.I), 0.85),
    (re.compile(r"\bverify\s+(?:your|the)\s+(?:account|number|identity)\b", re.I), 0.8),
    (re.compile(r"\bbkash\s*(?:helpline|help\s*line|customer\s*care|support)\b", re.I), 0.85),
    (re.compile(r"\bcall\s+(?:this|the\s+following)\s+number\b", re.I), 0.7),
    (re.compile(r"\bclick\s+(?:this|the)\s+link\b", re.I), 0.7),
    (re.compile(r"\bwon\s+(?:a\s+)?(?:prize|lottery|reward)\b", re.I), 0.7),
    (re.compile(r"\bkyc\b|\baccount\s*verification\b|ভেরিফাই", re.I), 0.7),
    (re.compile(r"\bsocial\s*engineering\b|\bphishing\b|\bscam\b|\bscammer\b", re.I), 0.9),
    (re.compile(r"\basked\s+(?:for|me\s+to\s+share)\b", re.I), 0.5),
    (re.compile(r"\bsomeone\s+(?:is\s+)?(?:asking|calling|pretending)\b", re.I), 0.6),
]

_WRONG_TRANSFER_PATTERNS: List[Tuple[re.Pattern[str], float]] = [
    (re.compile(r"\bwrong\s+(?:number|person|account|recipient)\b", re.I), 0.95),
    (re.compile(r"\bsent\s+(?:it\s+)?to\s+the\s+wrong\b", re.I), 0.85),
    (re.compile(r"\bby\s+mistake\b|\baccidentally\b|\binadvertently\b|ভুলে", re.I), 0.8),
    (re.compile(r"\bmis[- ]?sent\b|\bsent\s+to\s+the\s+wrong\b", re.I), 0.9),
    (re.compile(r"\bsent\s+(?:money|cash|taka|amount)\s+to\b", re.I), 0.4),
]

_PAYMENT_FAILED_PATTERNS: List[Tuple[re.Pattern[str], float]] = [
    (re.compile(r"\bpayment\s+failed\b|\btransaction\s+failed\b", re.I), 0.95),
    (re.compile(r"\btransaction\s+(?:didn['’]?t|did\s+not)\s+(?:go\s+through|complete|process)\b", re.I), 0.9),
    (re.compile(r"\bpay(?:ment)?\s+(?:was\s+)?unsuccessful\b", re.I), 0.9),
    (re.compile(r"\bbalance\s+(?:was\s+)?(?:deducted|debited|taken)\b", re.I), 0.7),
    (re.compile(r"\bmoney\s+(?:was\s+)?(?:deducted|debited|taken)\s+(?:but|however)\b", re.I), 0.85),
    (re.compile(r"\b(?:deducted|debited)\s+(?:but|however)\b", re.I), 0.85),
    (re.compile(r"\bdouble\s+charge(?:d)?\b|\bcharged\s+twice\b", re.I), 0.8),
    (re.compile(r"\bকেটে\s*নিয়েছে\b|\bকাটা\s*হয়েছে\b", re.I), 0.8),
    (re.compile(r"\bপেমেন্ট\s*(?:ফেইল|ব্যর্থ|বিফল)\b|\bলেনদেন\s*(?:ফেইল|ব্যর্থ|বিফল)\b", re.I), 0.95),
    (re.compile(r"\bটাকা\s*কেটে\s*নিয়েছে\b|\bব্যালেন্স\s*থেকে\s*কেটে\b", re.I), 0.85),
    (re.compile(r"\bbut\s+(?:didn['’]?t|did\s+not)\s+receive\b", re.I), 0.7),
    (re.compile(r"\bnot\s+credited\b|\bnot\s+received\b", re.I), 0.6),
]

_REFUND_PATTERNS: List[Tuple[re.Pattern[str], float]] = [
    (re.compile(r"\brefund\b|\brefund\s+request\b|ফেরত", re.I), 0.85),
    (re.compile(r"\bmoney\s+back\b|\bget\s+(?:my\s+)?money\s+back\b", re.I), 0.85),
    (re.compile(r"\bcancel\s+(?:my\s+)?(?:order|payment|transaction)\b", re.I), 0.7),
    (re.compile(r"\bchanged\s+my\s+mind\b|\bdon['’]?t\s+want\b", re.I), 0.6),
    (re.compile(r"\breturn\s+(?:my\s+)?(?:money|amount|payment)\b", re.I), 0.85),
    (re.compile(r"\bplease\s+refund\b", re.I), 0.6),
]

# Tie-break priority: earlier wins when scores are tied. Iteration order
# is also used as the tie-break rank, so a precomputed index is enough.
_TIE_PRIORITY: List[CaseType] = [
    "phishing_or_social_engineering",
    "payment_failed",
    "wrong_transfer",
    "refund_request",
    "other",
]
_TIE_PRIORITY_INDEX: Dict[CaseType, int] = {c: i for i, c in enumerate(_TIE_PRIORITY)}

# Cue regexes used by severity derivation (hoisted to module scope).
_BALANCE_DEDUCTION_RE = re.compile(
    r"\b(?:deducted|debited|taken)\b|কেটে\s*নিয়েছে|কাটা\s*হয়েছে",
    re.IGNORECASE,
)
_DISPUTE_CUE_RE = re.compile(
    r"\b(?:but|didn['’]?t|did\s+not|never)\s+(?:receive|get|deliver|arrive)\b"
    r"|\bmerchant\s+didn['’]?t\b",
    re.IGNORECASE,
)
_AMOUNT_RE = re.compile(
    r"(?P<amt>\d{1,3}(?:[,\s]\d{3})+|\d+(?:\.\d+)?)\s*(?:taka|tk|৳|bdt|usd|dollars?)?",
    re.I,
)


def _extract_amount(text: str) -> Optional[float]:
    """Return the first numeric amount in the message, or None."""
    m = _AMOUNT_RE.search(text)
    if not m:
        return None
    raw = m.group("amt").replace(",", "").replace(" ", "")
    try:
        return float(raw)
    except ValueError:
        return None


def _score(patterns: List[Tuple[re.Pattern[str], float]], text: str) -> Tuple[float, int]:
    """Return (capped_summed_score, pattern_hits)."""
    total = 0.0
    hits = 0
    for pattern, weight in patterns:
        if pattern.search(text):
            total += weight
            hits += 1
    return (min(total, 1.0), hits)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _amount_phrase(amount: float) -> str:
    n = int(amount) if amount.is_integer() else amount
    return f"{n} taka"


def _build_summary(
    message: str,
    case_type: CaseType,
    amount: Optional[float],
) -> str:
    if case_type == "phishing_or_social_engineering":
        return (
            "Customer reports being contacted by a party requesting sensitive "
            "credentials; route to fraud risk for human review."
        )
    if case_type == "wrong_transfer":
        amt = f" {_amount_phrase(amount)}" if amount else ""
        return (
            f"Customer reports sending{amt} to the wrong recipient and asks for help "
            "recovering the funds."
        )
    if case_type == "payment_failed":
        return (
            "Customer reports a failed transaction and a possible balance deduction; "
            "the payments team should investigate the transaction status."
        )
    if case_type == "refund_request":
        if amount:
            return (
                f"Customer requests a refund of {_amount_phrase(amount)}; "
                "review the original transaction before processing."
            )
        return "Customer requests a refund of a recent transaction."
    return "Customer submitted a support ticket that does not match a known case type."


@dataclass
class Classification:
    case_type: CaseType
    severity: Severity
    department: Department
    agent_summary: str
    human_review_required: bool
    confidence: float


def classify(message: str, locale: Optional[str] = None) -> Classification:
    """Classify a customer message into case_type / severity / department."""
    text = _norm(message)
    lowered = text.lower()

    scores: Dict[CaseType, Tuple[float, int]] = {
        "phishing_or_social_engineering": _score(_PHISHING_PATTERNS, lowered),
        "payment_failed": _score(_PAYMENT_FAILED_PATTERNS, lowered),
        "wrong_transfer": _score(_WRONG_TRANSFER_PATTERNS, lowered),
        "refund_request": _score(_REFUND_PATTERNS, lowered),
    }

    # Pick highest scorer; on ties, the earlier entry in _TIE_PRIORITY
    # wins (which is also the order we iterate in, so the first time we
    # see the max score we keep it).
    best_case: CaseType = "other"
    best_score = -1.0
    best_hits = 0
    for case_type in _TIE_PRIORITY:
        if case_type == "other":
            continue
        score, hits = scores[case_type]
        if score > best_score + 1e-6:
            best_score = score
            best_hits = hits
            best_case = case_type

    if best_score <= 0.0:
        best_case = "other"
        best_hits = 0

    case_type = best_case
    amount = _extract_amount(text)

    # ----- Severity -------------------------------------------------
    if case_type == "phishing_or_social_engineering":
        severity: Severity = "critical"
    elif case_type == "wrong_transfer":
        severity = "high" if (amount is not None and amount >= 1000) else "medium"
    elif case_type == "payment_failed":
        severity = "high" if _BALANCE_DEDUCTION_RE.search(lowered) else "medium"
    elif case_type == "refund_request":
        severity = "medium" if _DISPUTE_CUE_RE.search(lowered) else "low"
    else:
        severity = "low"

    # ----- Department ----------------------------------------------
    if case_type == "phishing_or_social_engineering":
        department: Department = "fraud_risk"
    elif case_type == "payment_failed":
        department = "payments_ops"
    elif case_type == "wrong_transfer":
        department = "dispute_resolution"
    elif case_type == "refund_request":
        department = (
            "dispute_resolution" if severity == "medium" else "customer_support"
        )
    else:
        department = "customer_support"

    human_review_required = (
        severity == "critical" or case_type == "phishing_or_social_engineering"
    )

    if case_type == "other":
        confidence = 0.5
    else:
        confidence = min(0.55 + 0.1 * min(best_hits, 4), 0.95)

    summary = _build_summary(text, case_type, amount)

    return Classification(
        case_type=case_type,
        severity=severity,
        department=department,
        agent_summary=summary,
        human_review_required=human_review_required,
        confidence=round(confidence, 2),
    )