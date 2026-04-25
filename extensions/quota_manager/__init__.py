import os

from .manager import QuotaManager
from .models import (
    BASELINE_TOKENS,
    ClaudeOperation,
    OperationType,
    QuotaDecision,
    UsageEntry,
    WindowSnapshot,
    Zone,
)

__all__ = [
    "QuotaManager",
    "OperationType",
    "QuotaDecision",
    "WindowSnapshot",
    "ClaudeOperation",
    "UsageEntry",
    "Zone",
    "BASELINE_TOKENS",
    "get_manager",
]


def get_manager() -> QuotaManager:
    return QuotaManager(
        state_path=os.environ.get("QUOTA_STATE_PATH", "extensions/quota_manager/quota_state.json"),
        window_limit=int(os.environ.get("QUOTA_WINDOW_LIMIT", "22000")),
    )
