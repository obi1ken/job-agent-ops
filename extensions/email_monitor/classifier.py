import re
from enum import Enum


class EmailClass(str, Enum):
    INTERVIEW_INVITE = "INTERVIEW_INVITE"
    REJECTION        = "REJECTION"
    OFFER            = "OFFER"
    INFO_REQUEST     = "INFO_REQUEST"
    UNKNOWN          = "UNKNOWN"


STATUS_MAP: dict[EmailClass, str] = {
    EmailClass.INTERVIEW_INVITE: "Interview",
    EmailClass.REJECTION:        "Rejected",
    EmailClass.OFFER:            "Offer",
    EmailClass.INFO_REQUEST:     "Responded",
    EmailClass.UNKNOWN:          "Responded",
}

_OFFER_PATTERNS = [
    r"offer\s+of\s+employment",
    r"job\s+offer",
    r"formal\s+offer",
    r"pleased\s+to\s+offer",
    r"we\s+(?:would\s+like\s+to\s+)?offer\s+you",
]

_INTERVIEW_PATTERNS = [
    r"interview",
    r"invite.*(?:chat|call|meet)",
    r"(?:schedule|book).*(?:call|meeting)",
    r"next\s+steps",
    r"virtual\s+(?:meeting|session)",
    r"video\s+call",
    r"telephone\s+(?:screen|interview)",
    r"assessment\s+centre",
]

_REJECTION_SUBJECT = [
    r"unfortunately",
    r"not\s+(?:been\s+)?successful",
    r"on\s+this\s+occasion",
    r"application\s+unsuccessful",
]

_REJECTION_BODY = [
    r"not\s+(?:been\s+)?selected",
    r"moving\s+forward\s+with\s+other\s+candidates",
    r"difficult\s+decision",
    r"keep\s+your\s+(?:cv|resume)\s+on\s+file",
    r"we\s+(?:will\s+not|won't)\s+be\s+(?:moving|progressing|taking)",
]

_INFO_REQUEST_PATTERNS = [
    r"(?:additional|further|more)\s+information",
    r"right\s+to\s+work",
    r"eligibility\s+to\s+work",
    r"document",
    r"reference",
    r"salary\s+expectation",
    r"notice\s+period",
    r"could\s+you\s+(?:please\s+)?(?:confirm|provide|send)",
]


def classify_email(subject: str, body: str, use_claude: bool = False) -> EmailClass:
    result = _classify_rule_based(subject, body)
    if result == EmailClass.UNKNOWN and use_claude:
        return _classify_with_claude(subject, body)
    return result


def _classify_rule_based(subject: str, body: str) -> EmailClass:
    body_excerpt = body[:2000]
    # Priority order: OFFER > INTERVIEW_INVITE > REJECTION > INFO_REQUEST
    if _match(subject, _OFFER_PATTERNS) or _match(body_excerpt, _OFFER_PATTERNS):
        return EmailClass.OFFER
    if _match(subject, _INTERVIEW_PATTERNS) or _match(body_excerpt, _INTERVIEW_PATTERNS):
        return EmailClass.INTERVIEW_INVITE
    if _match(subject, _REJECTION_SUBJECT) or _match(body_excerpt, _REJECTION_BODY):
        return EmailClass.REJECTION
    if _match(subject, _INFO_REQUEST_PATTERNS) or _match(body_excerpt, _INFO_REQUEST_PATTERNS):
        return EmailClass.INFO_REQUEST
    return EmailClass.UNKNOWN


def _classify_with_claude(subject: str, body: str) -> EmailClass:
    raise NotImplementedError(
        "Claude-based classification not yet implemented. "
        "Set ANTHROPIC_API_KEY and implement this stub when needed."
    )


def _match(text: str, patterns: list[str]) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in patterns)
