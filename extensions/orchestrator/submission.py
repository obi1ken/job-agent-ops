"""Post-approval submission — Phase 2 stub.

Appends the application row to data/applications.md and notifies Discord.
No web portal automation (Phase 3).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from extensions.deadline_manager.applications_reader import ApplicationsReader
from extensions.notifications import DiscordNotifier
from extensions.notifications.events import JobEvent

from .approval_store import PendingApproval
from .config import ProfileConfig


def submit_approved(pending: PendingApproval, config: ProfileConfig) -> bool:
    """Log approved application to data/applications.md and notify Discord.

    Returns True on success.
    """
    try:
        append_application_row(config.applications_md_path, pending)
    except Exception as exc:
        raise RuntimeError(f"Failed to append to applications.md: {exc}") from exc

    try:
        notifier = DiscordNotifier()
        notifier.send(
            JobEvent.CV_READY,
            company=pending.company,
            role=pending.role,
            track=pending.track,
            score=pending.score,
            cv_path=pending.cv_path,
        )
    except Exception:
        pass  # Discord failure should not fail the submission

    return True


def append_application_row(path: Path, pending: PendingApproval) -> None:
    """Append one row to the applications.md table.

    Idempotent: skips if a row with the same company+role+today already exists.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Check for duplicate
    if path.exists():
        try:
            rows = ApplicationsReader(str(path)).read_all()
            for row in rows:
                if (
                    row.company_display.lower() == pending.company.lower()
                    and row.role_display.lower() == pending.role.lower()
                    and str(row.date_applied) == today
                ):
                    return  # already logged
        except Exception:
            pass  # if reader fails, still append — better a dup than a miss

    new_row = (
        f"| {today} | {pending.company} | {pending.role} | {pending.track} "
        f"| {pending.score} | {pending.portal} | Applied | — | {pending.job_url or ''} |"
    )

    with path.open("a", encoding="utf-8") as f:
        f.write(new_row + "\n")
