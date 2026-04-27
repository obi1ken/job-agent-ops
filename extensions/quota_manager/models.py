from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


class OperationType(IntEnum):
    INTERVIEW_INVITE_RESPONSE = 1
    OFFER_PROCESSING          = 1
    JD_SCORING_URGENT         = 2
    CV_TAILORING_PRIORITY     = 2
    COVER_LETTER_PRIORITY     = 2
    JD_SCORING_STANDARD       = 3
    CV_TAILORING_STANDARD     = 3
    COVER_LETTER_STANDARD     = 3
    BATCH_DISCOVERY_SCAN      = 4


BASELINE_TOKENS: dict[str, int] = {
    "INTERVIEW_INVITE_RESPONSE": 12_000,
    "OFFER_PROCESSING":           3_000,
    "JD_SCORING_URGENT":          2_000,
    "CV_TAILORING_PRIORITY":      8_000,
    "COVER_LETTER_PRIORITY":      3_000,
    "JD_SCORING_STANDARD":        2_000,
    "CV_TAILORING_STANDARD":      8_000,
    "COVER_LETTER_STANDARD":      3_000,
    "BATCH_DISCOVERY_SCAN":       4_000,
}


class Zone:
    FREE       = "free"        # < 60%
    CAUTION    = "caution"     # 60–80%
    RESTRICTED = "restricted"  # 80–95%
    EMERGENCY  = "emergency"   # > 95%


@dataclass
class UsageEntry:
    timestamp_utc: str
    tokens: int
    operation: str  # OperationType name string


@dataclass
class WindowSnapshot:
    window_tokens: int
    window_limit: int
    used_pct: float
    zone: str
    oldest_entry_utc: Optional[str]


@dataclass
class QuotaDecision:
    allowed: bool
    zone: str
    used_pct: float
    window_tokens: int
    window_limit: int
    estimated_tokens: int
    reason: str


@dataclass
class ClaudeOperation:
    operation_type: OperationType
    estimated_tokens: int
    enqueued_at: str
    label: str
    payload: dict = field(default_factory=dict)
