from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from .applications_reader import extract_interview_datetime
from .models import AppLifecycle, ApplicationRow


class Action(str, Enum):
    NONE = "NONE"
    SEND_FOLLOW_UP = "SEND_FOLLOW_UP"
    EMIT_GHOST = "EMIT_GHOST"
    SCHEDULE_INTERVIEW = "SCHEDULE_INTERVIEW"
    SEND_PREP_REMINDER = "SEND_PREP_REMINDER"
    REQUEST_INTERVIEW_DATE = "REQUEST_INTERVIEW_DATE"
    MARK_REJECTED = "MARK_REJECTED"
    MARK_COMPLETED = "MARK_COMPLETED"


@dataclass
class Decision:
    action: Action
    new_lifecycle: AppLifecycle
    payload: dict = field(default_factory=dict)


# Statuses that are in the "open, waiting for reply" bucket
_OPEN_STATUSES = {"applied", "followed up", "followed_up", ""}
# Statuses that mean an interview has been set
_INTERVIEW_STATUSES = {"interview", "interview_invite", "interview invite"}
# Terminal statuses — no follow-up or ghost needed
_TERMINAL_STATUSES = {"rejected", "rejection", "offer", "ghost", "withdrawn", "completed"}


def decide(
    row: ApplicationRow,
    prior: dict,
    now_utc: datetime,
    follow_up_days: int,
    ghost_days: int,
    prep_lead_hours: int,
    tick_window_hours: int = 1,
) -> Decision:
    status = row.status_norm
    days_since = (now_utc.date() - row.date_applied).days

    # ── Terminal: nothing to do ───────────────────────────────────────────────
    if status in _TERMINAL_STATUSES:
        if status in ("rejected", "rejection"):
            return Decision(Action.MARK_REJECTED, AppLifecycle.REJECTED)
        return Decision(Action.MARK_COMPLETED, AppLifecycle.COMPLETED)

    # ── Interview flow ────────────────────────────────────────────────────────
    if status in _INTERVIEW_STATUSES:
        return _interview_decision(row, prior, now_utc, prep_lead_hours, tick_window_hours)

    # ── Open / follow-up flow ─────────────────────────────────────────────────
    if status in _OPEN_STATUSES:
        ghost_sent = prior.get("ghost_emitted_utc")
        follow_up_sent = prior.get("follow_up_sent_utc")

        # Once ghost is emitted the application is dead — no further actions
        if ghost_sent:
            return Decision(Action.NONE, AppLifecycle.GHOST)

        if days_since >= ghost_days:
            return Decision(
                Action.EMIT_GHOST,
                AppLifecycle.GHOST,
                {"days_since_applied": days_since},
            )

        if not follow_up_sent and days_since >= follow_up_days:
            return Decision(
                Action.SEND_FOLLOW_UP,
                AppLifecycle.FOLLOWED_UP,
                {"days_since_applied": days_since},
            )

    return Decision(Action.NONE, _current_lifecycle(prior))


def _interview_decision(
    row: ApplicationRow,
    prior: dict,
    now_utc: datetime,
    prep_lead_hours: int,
    tick_window_hours: int,
) -> Decision:
    stored_dt_str: Optional[str] = prior.get("interview_datetime_utc")
    prep_sent = prior.get("prep_reminder_sent_utc")

    # Parse and store interview datetime if not yet saved
    if not stored_dt_str:
        parsed = extract_interview_datetime(row.notes)
        if parsed:
            return Decision(
                Action.SCHEDULE_INTERVIEW,
                AppLifecycle.INTERVIEW_SCHEDULED,
                {"interview_datetime_utc": parsed.isoformat()},
            )
        # No datetime in notes — nudge Charles (rate-limited via caller checking prior state)
        return Decision(
            Action.REQUEST_INTERVIEW_DATE,
            AppLifecycle.INTERVIEW_SCHEDULED,
            {},
        )

    if prep_sent:
        return Decision(Action.NONE, AppLifecycle.PREP_SENT)

    # Fire prep reminder within the tick window straddling prep_lead_hours before
    try:
        interview_dt = datetime.fromisoformat(stored_dt_str)
    except ValueError:
        return Decision(Action.NONE, AppLifecycle.INTERVIEW_SCHEDULED)

    hours_until = (interview_dt - now_utc).total_seconds() / 3600
    low = prep_lead_hours - 1
    high = prep_lead_hours + tick_window_hours
    if low <= hours_until <= high:
        return Decision(
            Action.SEND_PREP_REMINDER,
            AppLifecycle.PREP_SENT,
            {"hours_until_interview": round(hours_until, 1)},
        )

    return Decision(Action.NONE, AppLifecycle.INTERVIEW_SCHEDULED)


def _current_lifecycle(prior: dict) -> AppLifecycle:
    raw = prior.get("lifecycle", "APPLIED")
    try:
        return AppLifecycle(raw)
    except ValueError:
        return AppLifecycle.APPLIED
