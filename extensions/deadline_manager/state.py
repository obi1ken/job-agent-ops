import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .models import ApplicationKey

_STATE_FILE = "deadline_state.json"
_VERSION = 1

_ENTRY_DEFAULTS = {
    "lifecycle": "APPLIED",
    "first_seen_utc": None,
    "follow_up_sent_utc": None,
    "ghost_emitted_utc": None,
    "interview_datetime_utc": None,
    "prep_reminder_sent_utc": None,
    "interview_date_request_sent_utc": None,
}


class DeadlineState:
    def __init__(self, state_dir: str):
        self._path = Path(state_dir) / _STATE_FILE
        self._data = self._load()

    def get(self, key: ApplicationKey) -> dict:
        return dict(self._data["entries"].get(key.serialize(), {}))

    def set_field(self, key: ApplicationKey, field: str, value: Any) -> None:
        k = key.serialize()
        if k not in self._data["entries"]:
            entry = dict(_ENTRY_DEFAULTS)
            entry["first_seen_utc"] = datetime.now(timezone.utc).isoformat()
            self._data["entries"][k] = entry
        self._data["entries"][k][field] = value
        self._save()

    def ensure_seen(self, key: ApplicationKey) -> None:
        k = key.serialize()
        if k not in self._data["entries"]:
            entry = dict(_ENTRY_DEFAULTS)
            entry["first_seen_utc"] = datetime.now(timezone.utc).isoformat()
            self._data["entries"][k] = entry
            self._save()

    def all_keys(self) -> set[str]:
        return set(self._data["entries"].keys())

    def prune(self, live_keys: set[str]) -> int:
        stale = self.all_keys() - live_keys
        for k in stale:
            del self._data["entries"][k]
        if stale:
            self._save()
        return len(stale)

    def set_last_tick(self, now_utc: datetime) -> None:
        self._data["last_tick_utc"] = now_utc.isoformat()
        self._save()

    def _load(self) -> dict:
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text(encoding="utf-8"))
                if raw.get("version") == _VERSION:
                    return {
                        "last_tick_utc": raw.get("last_tick_utc"),
                        "entries": raw.get("entries", {}),
                    }
            except (json.JSONDecodeError, KeyError):
                pass
        return {"last_tick_utc": None, "entries": {}}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".json.tmp")
        payload = {
            "version": _VERSION,
            "last_tick_utc": self._data["last_tick_utc"],
            "entries": self._data["entries"],
        }
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self._path)
