import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path


class DiscoveryState:
    def __init__(self, state_path: str):
        self._path = Path(state_path)
        self._data = self._load()

    def is_seen(self, source: str, external_id: str) -> bool:
        return external_id in self._data["seen"].get(source, {})

    def mark_seen(self, source: str, external_id: str) -> None:
        self._data["seen"].setdefault(source, {})[external_id] = (
            datetime.now(timezone.utc).isoformat()
        )

    def save(self) -> None:
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"version": 1, "seen": self._data["seen"]}, indent=2))
        os.replace(tmp, self._path)

    def prune(self, keep_days: int = 30) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)
        removed = 0
        for source in self._data["seen"]:
            stale = [
                eid for eid, ts in self._data["seen"][source].items()
                if _parse_ts(ts) < cutoff
            ]
            for eid in stale:
                del self._data["seen"][source][eid]
                removed += 1
        return removed

    def _load(self) -> dict:
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text())
                return {"seen": raw.get("seen", {})}
            except (json.JSONDecodeError, KeyError):
                pass
        return {"seen": {}}


def _parse_ts(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
