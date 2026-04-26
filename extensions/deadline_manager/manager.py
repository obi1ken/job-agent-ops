import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from .applications_reader import ApplicationsReader, DeadlineManagerError
from .lifecycle import Action, decide
from .models import AppLifecycle, ApplicationRow, TickResult
from .notifier import (
    send_follow_up_reminder,
    send_ghost,
    send_interview_date_missing,
    send_prep_reminder,
)
from .state import DeadlineState

_DEFAULT_STATE_DIR = "extensions/deadline_manager"
_DEFAULT_FOLLOW_UP_DAYS = 7
_DEFAULT_GHOST_DAYS = 14
_DEFAULT_PREP_LEAD_HOURS = 24
_DEFAULT_TICK_WINDOW_HOURS = 1
_DATE_REQUEST_COOLDOWN_HOURS = 48


class DeadlineManager:
    def __init__(
        self,
        applications_md_path: str,
        state_dir: str = _DEFAULT_STATE_DIR,
        follow_up_days: int = _DEFAULT_FOLLOW_UP_DAYS,
        ghost_days: int = _DEFAULT_GHOST_DAYS,
        prep_lead_hours: int = _DEFAULT_PREP_LEAD_HOURS,
        tick_window_hours: int = _DEFAULT_TICK_WINDOW_HOURS,
    ):
        self._reader = ApplicationsReader(applications_md_path)
        self._state = DeadlineState(state_dir)
        self._follow_up_days = follow_up_days
        self._ghost_days = ghost_days
        self._prep_lead_hours = prep_lead_hours
        self._tick_window_hours = tick_window_hours

    def tick(self) -> TickResult:
        now_utc = datetime.now(timezone.utc)
        result = TickResult()

        rows = self._reader.read_all()
        live_keys = {row.key.serialize() for row in rows}

        for row in rows:
            self._state.ensure_seen(row.key)
            prior = self._state.get(row.key)

            decision = decide(
                row,
                prior,
                now_utc,
                self._follow_up_days,
                self._ghost_days,
                self._prep_lead_hours,
                self._tick_window_hours,
            )

            if decision.action == Action.NONE:
                continue

            try:
                self._dispatch(row, decision, prior, now_utc, result)
            except Exception as exc:
                result.errors.append(f"{row.key.serialize()}: {exc}")

        result.pruned = self._state.prune(live_keys)
        self._state.set_last_tick(now_utc)
        return result

    def _dispatch(
        self,
        row: ApplicationRow,
        decision,
        prior: dict,
        now_utc: datetime,
        result: TickResult,
    ) -> None:
        key = row.key
        action = decision.action
        payload = decision.payload

        if action == Action.SEND_FOLLOW_UP:
            send_follow_up_reminder(row, payload.get("days_since_applied", 0))
            self._state.set_field(key, "follow_up_sent_utc", now_utc.isoformat())
            self._state.set_field(key, "lifecycle", AppLifecycle.FOLLOWED_UP.value)
            result.follow_ups_sent.append(key.serialize())

        elif action == Action.EMIT_GHOST:
            send_ghost(row, payload.get("days_since_applied", 0))
            self._state.set_field(key, "ghost_emitted_utc", now_utc.isoformat())
            self._state.set_field(key, "lifecycle", AppLifecycle.GHOST.value)
            result.ghosts_emitted.append(key.serialize())

        elif action == Action.SCHEDULE_INTERVIEW:
            self._state.set_field(key, "interview_datetime_utc", payload["interview_datetime_utc"])
            self._state.set_field(key, "lifecycle", AppLifecycle.INTERVIEW_SCHEDULED.value)
            result.interviews_scheduled.append(key.serialize())

        elif action == Action.SEND_PREP_REMINDER:
            send_prep_reminder(row, payload.get("hours_until_interview", 0))
            self._state.set_field(key, "prep_reminder_sent_utc", now_utc.isoformat())
            self._state.set_field(key, "lifecycle", AppLifecycle.PREP_SENT.value)
            result.prep_reminders_sent.append(key.serialize())

        elif action == Action.REQUEST_INTERVIEW_DATE:
            last_request = prior.get("interview_date_request_sent_utc")
            if last_request:
                last_dt = datetime.fromisoformat(last_request)
                if (now_utc - last_dt) < timedelta(hours=_DATE_REQUEST_COOLDOWN_HOURS):
                    return  # still in cooldown
            send_interview_date_missing(row)
            self._state.set_field(key, "interview_date_request_sent_utc", now_utc.isoformat())
            self._state.set_field(key, "lifecycle", AppLifecycle.INTERVIEW_SCHEDULED.value)

        elif action == Action.MARK_REJECTED:
            self._state.set_field(key, "lifecycle", AppLifecycle.REJECTED.value)

        elif action == Action.MARK_COMPLETED:
            self._state.set_field(key, "lifecycle", AppLifecycle.COMPLETED.value)


def run_tick() -> TickResult:
    root = os.environ.get("PROJECT_ROOT", ".")
    apps_path = os.path.join(root, "data", "applications.md")
    state_dir = os.environ.get("DEADLINE_STATE_DIR", _DEFAULT_STATE_DIR)
    follow_up_days = int(os.environ.get("DEADLINE_FOLLOW_UP_DAYS", str(_DEFAULT_FOLLOW_UP_DAYS)))
    ghost_days = int(os.environ.get("DEADLINE_GHOST_DAYS", str(_DEFAULT_GHOST_DAYS)))
    prep_lead_hours = int(os.environ.get("DEADLINE_PREP_LEAD_HOURS", str(_DEFAULT_PREP_LEAD_HOURS)))

    return DeadlineManager(
        applications_md_path=apps_path,
        state_dir=state_dir,
        follow_up_days=follow_up_days,
        ghost_days=ghost_days,
        prep_lead_hours=prep_lead_hours,
    ).tick()
