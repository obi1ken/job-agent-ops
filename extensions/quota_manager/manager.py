import os
from typing import Optional

from .models import (
    BASELINE_TOKENS,
    ClaudeOperation,
    OperationType,
    QuotaDecision,
    WindowSnapshot,
)
from .policy import QuotaPolicy
from .queue import PendingQueue
from .window import RollingWindow

_DEFAULT_STATE_PATH = "extensions/quota_manager/quota_state.json"
_DEFAULT_LIMIT = 22_000   # 25% of 88k Max plan shared pool
_DEFAULT_WINDOW_HOURS = 5
_DEFAULT_STALE_MINUTES = 60


class QuotaManager:
    def __init__(
        self,
        state_path: Optional[str] = None,
        window_limit: Optional[int] = None,
        window_hours: Optional[int] = None,
    ):
        path = state_path or os.environ.get("QUOTA_STATE_PATH", _DEFAULT_STATE_PATH)
        hours = window_hours or int(os.environ.get("QUOTA_WINDOW_HOURS", str(_DEFAULT_WINDOW_HOURS)))
        self._limit = window_limit or int(os.environ.get("QUOTA_WINDOW_LIMIT", str(_DEFAULT_LIMIT)))
        self._window = RollingWindow(path, window_hours=hours)
        self._queue = PendingQueue(state_dir=os.path.dirname(path))

    def request(
        self,
        operation_type: OperationType,
        estimated_tokens: Optional[int] = None,
        label: str = "",
    ) -> QuotaDecision:
        tokens = estimated_tokens or self.estimate_tokens(operation_type)
        snap = self._window.snapshot(self._limit)
        return QuotaPolicy.evaluate(snap, operation_type, tokens)

    def record_usage(self, tokens_used: int, operation_type: OperationType) -> WindowSnapshot:
        self._window.record(tokens_used, operation_type)
        return self._window.snapshot(self._limit)

    def defer(self, op: ClaudeOperation) -> None:
        self._queue.push(op)

    def flush_queue(self) -> list[ClaudeOperation]:
        snap = self._window.snapshot(self._limit)
        return self._queue.pop_eligible(snap)

    def confirm_dequeued(self, op: ClaudeOperation) -> None:
        self._queue.confirm_dequeued(op)

    def drain_stale_queue(self, max_age_minutes: Optional[int] = None) -> list[ClaudeOperation]:
        minutes = max_age_minutes or int(os.environ.get("QUOTA_STALE_QUEUE_MINUTES", str(_DEFAULT_STALE_MINUTES)))
        return self._queue.drain_stale(minutes)

    def snapshot(self) -> WindowSnapshot:
        return self._window.snapshot(self._limit)

    def queue_depth(self) -> int:
        return len(self._queue)

    def estimate_tokens(
        self,
        operation_type: OperationType,
        input_text: Optional[str] = None,
    ) -> int:
        base = BASELINE_TOKENS.get(operation_type.name, 2_000)
        if input_text:
            base += len(input_text) // 4
        return base
