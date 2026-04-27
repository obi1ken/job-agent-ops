import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

STATE_FILE = "poll_state.json"
_PRUNE_EVERY = 100  # prune old IDs every N writes


class PollState:
    def __init__(self, state_dir: str):
        self._path = Path(state_dir) / STATE_FILE
        self._write_count = 0
        self._data = self._load()

    def is_processed(self, message_id: str) -> bool:
        return message_id in self._data["processed_ids"]

    def mark_processed(self, message_id: str) -> None:
        self._data["processed_ids"].add(message_id)
        self._data["last_poll_utc"] = datetime.now(timezone.utc).isoformat()
        self._write_count += 1
        if self._write_count % _PRUNE_EVERY == 0:
            self.prune_old_ids()
        self._save()

    def get_last_poll_time(self) -> Optional[datetime]:
        raw = self._data.get("last_poll_utc")
        if not raw:
            return None
        return datetime.fromisoformat(raw)

    def prune_old_ids(self, keep_days: int = 90) -> int:
        # IDs are added in insertion order; prune oldest beyond keep_days window.
        # We can't easily date individual IDs, so prune to a max count instead.
        max_ids = keep_days * 20  # rough cap: 20 emails/day
        ids = list(self._data["processed_ids"])
        if len(ids) > max_ids:
            pruned_count = len(ids) - max_ids
            self._data["processed_ids"] = set(ids[pruned_count:])
            self._save()
            return pruned_count
        return 0

    def _load(self) -> dict:
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text())
                return {
                    "last_poll_utc": raw.get("last_poll_utc"),
                    "processed_ids": set(raw.get("processed_ids", [])),
                }
            except (json.JSONDecodeError, KeyError):
                pass
        return {"last_poll_utc": None, "processed_ids": set()}

    def _save(self) -> None:
        tmp = self._path.with_suffix(".json.tmp")
        payload = {
            "version": 1,
            "last_poll_utc": self._data["last_poll_utc"],
            "processed_ids": list(self._data["processed_ids"]),
        }
        tmp.write_text(json.dumps(payload, indent=2))
        os.replace(tmp, self._path)
