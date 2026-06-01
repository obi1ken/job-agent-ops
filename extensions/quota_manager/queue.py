import heapq
import itertools
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from .models import ClaudeOperation, OperationType, WindowSnapshot
from .policy import QuotaPolicy

_OP_IDX = 3
_QUEUE_FILE = "pending_queue.json"
_VERSION = 1


class PendingQueue:
    def __init__(self, state_dir: Optional[str] = None):
        self._state_path = Path(state_dir or "extensions/quota_manager") / _QUEUE_FILE
        self._heap: list[tuple] = []
        self._counter = itertools.count()
        self._load()

    def push(self, op: ClaudeOperation) -> None:
        heapq.heappush(self._heap, (op.operation_type.value, next(self._counter), op.enqueued_at, op))
        self._save()

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
        self._save()

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
        if stale:
            self._save()
        return [op for op in stale if isinstance(op, ClaudeOperation)]

    def __len__(self) -> int:
        return len(self._heap)

    def peek_all(self) -> list[ClaudeOperation]:
        return [item[_OP_IDX] for item in sorted(self._heap)]

    def _save(self) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        items = []
        for item in sorted(self._heap):
            op = item[_OP_IDX]
            items.append({
                "operation_type": op.operation_type.name,
                "estimated_tokens": op.estimated_tokens,
                "enqueued_at": op.enqueued_at,
                "label": op.label,
                "payload": op.payload,
            })
        tmp = self._state_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"version": _VERSION, "items": items}, indent=2))
        os.replace(tmp, self._state_path)

    def _load(self) -> None:
        if not self._state_path.exists():
            return
        try:
            raw = json.loads(self._state_path.read_text())
            if raw.get("version") != _VERSION:
                return
            for item in raw.get("items", []):
                op = ClaudeOperation(
                    operation_type=OperationType[item["operation_type"]],
                    estimated_tokens=item["estimated_tokens"],
                    enqueued_at=item["enqueued_at"],
                    label=item["label"],
                    payload=item.get("payload", {}),
                )
                heapq.heappush(self._heap, (op.operation_type.value, next(self._counter), op.enqueued_at, op))
        except (json.JSONDecodeError, KeyError, ValueError):
            self._heap = []
