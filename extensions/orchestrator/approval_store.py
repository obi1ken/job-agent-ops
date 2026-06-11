from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

_STORE_FILE = "pending_approvals.json"
_VERSION = 1
_EXPIRE_DAYS = 7


class ApprovalState(str, Enum):
    AWAITING = "AWAITING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"
    SUBMITTED = "SUBMITTED"
    EXPIRED = "EXPIRED"


@dataclass
class PendingApproval:
    approval_id: str
    company: str
    role: str
    track: str
    score: float
    portal: str
    job_url: str
    cv_path: str
    cover_letter_path: str
    jd_path: str
    created_utc: str
    state: str                      # ApprovalState value
    state_changed_utc: str
    discord_message_id: Optional[str] = None
    defer_until_utc: Optional[str] = None
    tailoring_summary: dict = field(default_factory=dict)
    notes: str = ""
    stage: str = "DOCS"             # "INTEREST" (job match, no docs yet) | "DOCS"
    location: str = ""

    @staticmethod
    def create(
        company: str, role: str, track: str, score: float, portal: str,
        job_url: str, cv_path: str, cover_letter_path: str, jd_path: str,
        tailoring_summary: dict | None = None,
        stage: str = "DOCS",
        location: str = "",
    ) -> "PendingApproval":
        now = datetime.now(timezone.utc).isoformat()
        return PendingApproval(
            approval_id=str(uuid.uuid4()),
            company=company, role=role, track=track, score=score,
            portal=portal, job_url=job_url, cv_path=cv_path,
            cover_letter_path=cover_letter_path, jd_path=jd_path,
            created_utc=now, state=ApprovalState.AWAITING.value,
            state_changed_utc=now, tailoring_summary=tailoring_summary or {},
            stage=stage, location=location,
        )


class ApprovalStore:
    def __init__(self, state_dir: Path):
        self._path = state_dir / _STORE_FILE
        self._approvals: dict[str, PendingApproval] = {}
        self._load()

    def add(self, pending: PendingApproval) -> None:
        self._approvals[pending.approval_id] = pending
        self._save()

    def get(self, approval_id: str) -> Optional[PendingApproval]:
        return self._approvals.get(approval_id)

    def find_by_message_id(self, msg_id: str) -> Optional[PendingApproval]:
        for a in self._approvals.values():
            if a.discord_message_id == msg_id:
                return a
        return None

    def list_awaiting(self) -> list[PendingApproval]:
        return [a for a in self._approvals.values() if a.state == ApprovalState.AWAITING.value]

    def list_due_for_retry(self, now_utc: datetime) -> list[PendingApproval]:
        due = []
        for a in self._approvals.values():
            if a.state == ApprovalState.DEFERRED.value and a.defer_until_utc:
                try:
                    until = datetime.fromisoformat(a.defer_until_utc)
                    if now_utc >= until:
                        due.append(a)
                except ValueError:
                    pass
        return due

    def transition(
        self,
        approval_id: str,
        new_state: ApprovalState,
        *,
        notes: str = "",
        discord_message_id: Optional[str] = None,
        defer_until_utc: Optional[str] = None,
    ) -> Optional[PendingApproval]:
        a = self._approvals.get(approval_id)
        if a is None:
            return None
        changed = a.state != new_state.value
        a.state = new_state.value
        if changed:
            a.state_changed_utc = datetime.now(timezone.utc).isoformat()
        if notes:
            a.notes = notes
        if discord_message_id:
            a.discord_message_id = discord_message_id
        if defer_until_utc is not None:
            a.defer_until_utc = defer_until_utc
        self._save()
        return a

    def attach_documents(
        self,
        approval_id: str,
        cv_path: str,
        cover_letter_path: str,
        tailoring_summary: dict,
    ) -> Optional[PendingApproval]:
        """Attach generated documents and move the approval to the DOCS stage."""
        a = self._approvals.get(approval_id)
        if a is None:
            return None
        a.cv_path = cv_path
        a.cover_letter_path = cover_letter_path
        a.tailoring_summary = tailoring_summary
        a.stage = "DOCS"
        self._save()
        return a

    def expire_stale(self, now_utc: datetime, ttl_days: int = _EXPIRE_DAYS) -> list[str]:
        expired_ids = []
        for a in self._approvals.values():
            if a.state != ApprovalState.AWAITING.value:
                continue
            try:
                created = datetime.fromisoformat(a.created_utc)
                if (now_utc - created).days >= ttl_days:
                    a.state = ApprovalState.EXPIRED.value
                    a.state_changed_utc = now_utc.isoformat()
                    expired_ids.append(a.approval_id)
            except ValueError:
                pass
        if expired_ids:
            self._save()
        return expired_ids

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if raw.get("version") != _VERSION:
                return
            for item in raw.get("approvals", []):
                try:
                    a = PendingApproval(**item)
                    self._approvals[a.approval_id] = a
                except (TypeError, KeyError):
                    pass
        except (json.JSONDecodeError, KeyError):
            _backup_corrupt(self._path)

    def _save(self) -> None:
        tmp = self._path.with_suffix(".json.tmp")
        payload = {
            "version": _VERSION,
            "approvals": [asdict(a) for a in self._approvals.values()],
        }
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self._path)


def _backup_corrupt(path: Path) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    corrupt = path.with_name(f"{path.stem}.corrupt-{ts}.json")
    path.rename(corrupt)
