import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from .models import OperationType, UsageEntry, WindowSnapshot, Zone

_VERSION = 1


def _zone_for(used_pct: float) -> str:
    if used_pct < 0.60:
        return Zone.FREE
    if used_pct < 0.80:
        return Zone.CAUTION
    if used_pct < 0.95:
        return Zone.RESTRICTED
    return Zone.EMERGENCY


class RollingWindow:
    def __init__(self, state_path: str, window_hours: int = 5):
        self._path = Path(state_path)
        self._window_hours = window_hours
        self._entries: list[UsageEntry] = []
        self._load()

    def current_usage(self) -> int:
        self.prune()
        return sum(e.tokens for e in self._entries)

    def snapshot(self, window_limit: int) -> WindowSnapshot:
        total = self.current_usage()
        used_pct = total / window_limit if window_limit > 0 else 0.0
        oldest = self._entries[0].timestamp_utc if self._entries else None
        return WindowSnapshot(
            window_tokens=total,
            window_limit=window_limit,
            used_pct=used_pct,
            zone=_zone_for(used_pct),
            oldest_entry_utc=oldest,
        )

    def record(self, tokens: int, operation: OperationType) -> None:
        self._entries.append(UsageEntry(
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            tokens=tokens,
            operation=operation.name,
        ))
        self.save()

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".json.tmp")
        payload = {
            "version": _VERSION,
            "usage_log": [
                {"timestamp_utc": e.timestamp_utc, "tokens": e.tokens, "operation": e.operation}
                for e in self._entries
            ],
        }
        tmp.write_text(json.dumps(payload, indent=2))
        os.replace(tmp, self._path)

    def prune(self) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self._window_hours)
        before = len(self._entries)
        self._entries = [
            e for e in self._entries
            if _parse_ts(e.timestamp_utc) >= cutoff
        ]
        return before - len(self._entries)

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text())
            self._entries = [
                UsageEntry(
                    timestamp_utc=item["timestamp_utc"],
                    tokens=int(item["tokens"]),
                    operation=item["operation"],
                )
                for item in raw.get("usage_log", [])
            ]
        except (json.JSONDecodeError, KeyError, ValueError):
            self._entries = []


def _parse_ts(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
