import re
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class AppLifecycle(str, Enum):
    APPLIED = "APPLIED"
    FOLLOWED_UP = "FOLLOWED_UP"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    PREP_SENT = "PREP_SENT"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    GHOST = "GHOST"


@dataclass(frozen=True)
class ApplicationKey:
    company_slug: str   # lowercase alphanumeric
    role_slug: str      # lowercase alphanumeric, whitespace collapsed
    date_applied: str   # ISO YYYY-MM-DD

    def serialize(self) -> str:
        return f"{self.company_slug}|{self.role_slug}|{self.date_applied}"

    @staticmethod
    def from_parts(company: str, role: str, date_applied: str) -> "ApplicationKey":
        return ApplicationKey(
            company_slug=re.sub(r"[^a-z0-9]", "", company.lower()),
            role_slug=re.sub(r"[^a-z0-9]", "", " ".join(role.lower().split())),
            date_applied=date_applied,
        )


@dataclass
class ApplicationRow:
    key: ApplicationKey
    company_display: str
    role_display: str
    track: str
    score: str
    portal: str
    status_raw: str
    status_norm: str    # lowercased, stripped
    date_applied: date
    cv_version: str
    notes: str


@dataclass
class TickResult:
    follow_ups_sent: list[str] = field(default_factory=list)
    ghosts_emitted: list[str] = field(default_factory=list)
    interviews_scheduled: list[str] = field(default_factory=list)
    prep_reminders_sent: list[str] = field(default_factory=list)
    pruned: int = 0
    errors: list[str] = field(default_factory=list)
