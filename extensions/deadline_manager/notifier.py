from extensions.notifications import DiscordNotifier
from extensions.notifications.events import JobEvent

from .models import ApplicationRow


def send_follow_up_reminder(app: ApplicationRow, days_since_applied: int) -> None:
    notifier = DiscordNotifier()
    notifier.send(
        JobEvent.REPLY_RECEIVED,
        company=app.company_display,
        role=app.role_display,
        track=app.track,
        subject=f"Follow-up due — {days_since_applied} days since application",
        classifier="FOLLOW_UP_DUE",
    )


def send_ghost(app: ApplicationRow, days_since_applied: int) -> None:
    notifier = DiscordNotifier()
    notifier.send(
        JobEvent.GHOST,
        company=app.company_display,
        role=app.role_display,
        track=app.track,
        days=days_since_applied,
    )


def send_prep_reminder(app: ApplicationRow, hours_until_interview: float) -> None:
    notifier = DiscordNotifier()
    notifier.send(
        JobEvent.INTERVIEW_INVITE,
        company=app.company_display,
        role=app.role_display,
        track=app.track,
        date=f"In ~{round(hours_until_interview)}h",
    )


def send_interview_date_missing(app: ApplicationRow) -> None:
    notifier = DiscordNotifier()
    notifier.send(
        JobEvent.REPLY_RECEIVED,
        company=app.company_display,
        role=app.role_display,
        track=app.track,
        subject="Interview scheduled — add datetime to Notes (YYYY-MM-DD HH:MM)",
        classifier="DATE_MISSING",
    )
