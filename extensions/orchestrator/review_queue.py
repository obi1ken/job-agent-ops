"""Serial review queue — scored jobs wait here and are presented to Charles
one at a time. Approve → documents; reject → the next queued job surfaces.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_STORE_FILE = "review_queue.json"
_VERSION = 1

# Entry statuses
QUEUED = "QUEUED"          # scored above threshold, waiting its turn
PRESENTED = "PRESENTED"    # Job Match embed posted, awaiting Charles
APPROVED = "APPROVED"      # Charles approved (docs flow took over)
REJECTED = "REJECTED"      # Charles rejected at either stage
EXPIRED = "EXPIRED"        # approval expired unanswered


@dataclass
class ReviewEntry:
    entry_id: str              # listing external_id
    company: str
    role: str
    track: str
    score: float
    portal: str
    job_url: str
    jd_path: str
    location: str = ""
    edms_platform: Optional[str] = None
    status: str = QUEUED
    approval_id: str = ""
    added_utc: str = ""
    status_changed_utc: str = ""


class ReviewQueue:
    def __init__(self, state_dir: Path):
        self._path = Path(state_dir) / _STORE_FILE
        self._entries: dict[str, ReviewEntry] = {}
        self._load()

    def add(self, entry: ReviewEntry) -> bool:
        """Queue a scored job. Returns False if already known (dedup)."""
        if entry.entry_id in self._entries:
            return False
        now = datetime.now(timezone.utc).isoformat()
        entry.added_utc = entry.added_utc or now
        entry.status_changed_utc = now
        self._entries[entry.entry_id] = entry
        self._save()
        return True

    def next_queued(self) -> Optional[ReviewEntry]:
        """Highest score first; FIFO within equal scores."""
        queued = [e for e in self._entries.values() if e.status == QUEUED]
        if not queued:
            return None
        return sorted(queued, key=lambda e: (-e.score, e.added_utc))[0]

    def mark(self, entry_id: str, status: str, approval_id: str = "") -> None:
        e = self._entries.get(entry_id)
        if e is None:
            return
        e.status = status
        if approval_id:
            e.approval_id = approval_id
        e.status_changed_utc = datetime.now(timezone.utc).isoformat()
        self._save()

    def mark_by_approval(self, approval_id: str, status: str) -> Optional[ReviewEntry]:
        for e in self._entries.values():
            if e.approval_id == approval_id:
                self.mark(e.entry_id, status)
                return e
        return None

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for e in self._entries.values():
            out[e.status] = out.get(e.status, 0) + 1
        return out

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if raw.get("version") != _VERSION:
                return
            for item in raw.get("entries", []):
                try:
                    e = ReviewEntry(**item)
                    self._entries[e.entry_id] = e
                except TypeError:
                    pass
        except (json.JSONDecodeError, KeyError):
            pass

    def _save(self) -> None:
        tmp = self._path.with_suffix(".json.tmp")
        payload = {
            "version": _VERSION,
            "entries": [asdict(e) for e in self._entries.values()],
        }
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self._path)
