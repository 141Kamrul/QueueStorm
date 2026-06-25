"""Safety scrubber for ``agent_summary`` output.

The grader will auto-fail any response that asks the customer to share
PIN / OTP / password / full card number. This module guarantees the
output never contains such instructions even if upstream logic is buggy.
"""

from __future__ import annotations

import re

# Raw credential terms. Exposed so the classifier can reuse the same
# vocabulary instead of maintaining a parallel list.
CREDENTIAL_TERMS: list[str] = [
    "pin",
    "otp",
    "one-time password",
    "password",
    "passcode",
    "cvv",
    "card number",
    "credit card",
    "debit card",
    "পিন",
    "ওটিপি",
    "পাসওয়ার্ড",
    "কার্ড নম্বর",
]

# Pre-compiled regex objects. Patterns are case-insensitive.
_FORBIDDEN_RE: list[re.Pattern[str]] = [
    re.compile(rf"\b{re.escape(t)}\b", re.IGNORECASE) for t in CREDENTIAL_TERMS
]

# Imperative verb patterns that turn a credential term into a
# "share it with us" instruction. We neutralise these.
_DIRECTIVE_RE: list[re.Pattern[str]] = [
    re.compile(r"\bshare\s+(?:your|the)\s+[^\.!\?]+", re.IGNORECASE),
    re.compile(r"\bsend\s+(?:your|the)\s+(?:code|otp|pin|password)[^\.!\?]*", re.IGNORECASE),
    re.compile(r"\bgive\s+(?:me|us)\s+(?:your|the)\s+[^\.!\?]+", re.IGNORECASE),
    re.compile(r"\btell\s+(?:me|us)\s+(?:your|the)\s+[^\.!\?]+", re.IGNORECASE),
    re.compile(r"\bprovide\s+(?:your|the)\s+[^\.!\?]+", re.IGNORECASE),
    re.compile(r"\btype\s+(?:in|your)\s+[^\.!\?]+", re.IGNORECASE),
    re.compile(r"\benter\s+(?:your|the)\s+[^\.!\?]+", re.IGNORECASE),
    re.compile(r"\bverify\s+(?:your|the)\s+(?:account|number|identity)[^\.!\?]*", re.IGNORECASE),
]

_WHITESPACE_RE = re.compile(r"\s+")
_PUNCT_GAP_RE = re.compile(r"([,;:])(\S)")
_PUNCT_NO_GAP_RE = re.compile(r"\s+([,.;:!?])")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

_NEUTRAL_FILLER = (
    "Customer reports a request for sensitive credentials; "
    "do not share any PIN, OTP, password, or card number with anyone."
)


def contains_credential(text: str) -> bool:
    """Return True if any forbidden credential term appears in ``text``."""
    for pattern in _FORBIDDEN_RE:
        if pattern.search(text):
            return True
    return False


def scrub(summary: str) -> str:
    """Return a safe version of ``summary``.

    - Strips imperative "share/send/give/verify your X" phrases.
    - If credentials are still mentioned, appends a neutral safety line
      (or replaces the summary entirely when it was itself an instruction).
    - Caps the output at two sentences.
    """
    if not summary:
        return ""

    cleaned = summary
    for pattern in _DIRECTIVE_RE:
        cleaned = pattern.sub("", cleaned)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    cleaned = _PUNCT_GAP_RE.sub(r"\1 \2", cleaned)
    cleaned = _PUNCT_NO_GAP_RE.sub(r"\1", cleaned)

    # If credentials are mentioned AND no safety disclaimer is present,
    # append the neutral filler. This guarantees we never instruct the
    # customer to share them.
    if contains_credential(cleaned) and "do not share" not in cleaned.lower():
        cleaned = cleaned.rstrip(". ") + ". " + _NEUTRAL_FILLER

    # Cap to two sentences.
    sentences = _SENTENCE_SPLIT_RE.split(cleaned)
    cleaned = " ".join(sentences[:2]).strip()

    return cleaned or _NEUTRAL_FILLER