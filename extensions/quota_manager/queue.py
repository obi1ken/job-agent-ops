import heapq
import itertools
from datetime import datetime, timedelta, timezone

from .models import ClaudeOperation, OperationType, WindowSnapshot
from .policy import QuotaPolicy

# Tuple layout: (priority, counter, enqueued_at, op)
# The counter guarantees unique ordering so ClaudeOperation is never compared.
_OP_IDX = 3


class PendingQueue:
    def __init__(self):
        self._heap: list[tuple] = []
        self._counter = itertools.count()

    def push(self, op: ClaudeOperation) -> None:
        heapq.heappush(self._heap, (op.operation_type.value, next(self._counter), op.enqueued_at, op))

    def pop_eligible(self, snapshot: WindowSnapshot) -> list[ClaudeOperation]:
        eligible = []
        for item in sorted(self._heap):
            op = item[_OP_IDX]
            decision = QuotaPolicy.evaluate(snapshot, op.operation_type, op.estimated_tokens)
            if decision.allowed:
                eligible.append(op)
        return eligible

    def confirm_dequeued(self, op: ClaudeOperation) -> None:
        self._heap = [
            item for item in self._heap
            if not (item[_OP_IDX].operation_type == op.operation_type and item[_OP_IDX].enqueued_at == op.enqueued_at)
        ]
        heapq.heapify(self._heap)

    def drain_stale(self, max_age_minutes: int = 60) -> list[ClaudeOperation]:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
        stale, fresh = [], []
        for item in self._heap:
            op = item[_OP_IDX]
            try:
                enqueued = datetime.fromisoformat(op.enqueued_at)
            except ValueError:
                stale.append(op)
                continue
            (stale if enqueued < cutoff else fresh).append(item)
        self._heap = fresh
        heapq.heapify(self._heap)
        return [op for op in stale if isinstance(op, ClaudeOperation)]

    def __len__(self) -> int:
        return len(self._heap)

    def peek_all(self) -> list[ClaudeOperation]:
        return [item[_OP_IDX] for item in sorted(self._heap)]
