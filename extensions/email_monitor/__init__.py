import logging
import os
from datetime import datetime, timezone
from typing import Optional

from .classifier import EmailClass, classify_email
from .gmail_client import GmailClient
from .notifier_bridge import DiscordNotificationError, dispatch_notification
from .state import PollState
from .tracker_updater import TrackerUpdateError, TrackerUpdater

log = logging.getLogger(__name__)


class EmailMonitorError(Exception):
    pass


class EmailMonitor:
    def __init__(self, credentials_path: str, token_path: str, data_dir: str, state_dir: str):
        self._gmail = GmailClient(credentials_path, token_path)
        self._state = PollState(state_dir)
        self._tracker = TrackerUpdater(os.path.join(data_dir, "data", "applications.md"))
        self._max_results = int(os.environ.get("GMAIL_POLL_MAX_RESULTS", "50"))

    def authenticate(self) -> None:
        self._gmail.authenticate()

    def poll(self) -> list[dict]:
        results = []
        try:
            messages = self._gmail.list_unread_messages(max_results=self._max_results)
        except Exception as exc:
            raise EmailMonitorError(f"Gmail list failed: {exc}") from exc

        for msg in messages:
            message_id = msg["id"]
            if self._state.is_processed(message_id):
                continue
            result = self._process_one(message_id)
            if result:
                results.append(result)

        return results

    def _process_one(self, message_id: str) -> Optional[dict]:
        try:
            message = self._gmail.get_message(message_id)
        except Exception as exc:
            log.error("Failed to fetch message %s: %s", message_id, exc)
            return None

        from .classifier import STATUS_MAP
        email_class = classify_email(message["subject"], message["body_text"])
        new_status = STATUS_MAP[email_class]

        matched_company: Optional[str] = None
        try:
            matched_company = self._tracker.find_and_update(
                sender_email=message["sender"],
                sender_name=message["sender"],
                new_status=new_status,
                notes_suffix=f"Reply {datetime.now(timezone.utc).strftime('%Y-%m-%d')} {email_class.value}",
            )
        except TrackerUpdateError as exc:
            log.error("Tracker update failed for %s: %s — message left unread for retry", message_id, exc)
            return None

        role = ""  # role not extractable from email alone

        notified = False
        if matched_company is not None:
            try:
                dispatch_notification(
                    email_class=email_class,
                    company=matched_company,
                    role=role,
                    subject=message["subject"],
                    email_date=message["date"],
                )
                notified = True
            except DiscordNotificationError as exc:
                log.error("Discord notification failed for %s: %s", message_id, exc)
        else:
            log.debug("No application match for email %s — skipping notification", message_id)

        self._state.mark_processed(message_id)
        try:
            self._gmail.mark_as_read(message_id)
        except Exception as exc:
            log.warning("mark_as_read failed for %s: %s", message_id, exc)

        return {
            "message_id": message_id,
            "subject": message["subject"],
            "sender": message["sender"],
            "email_class": email_class.value,
            "company_matched": matched_company,
            "status_updated": new_status,
            "notified": notified,
        }


def run_poll() -> None:
    monitor = EmailMonitor(
        credentials_path=os.environ["GMAIL_CREDENTIALS_PATH"],
        token_path=os.environ["GMAIL_TOKEN_PATH"],
        data_dir=os.environ.get("PROJECT_ROOT", "."),
        state_dir=os.path.dirname(os.environ["GMAIL_TOKEN_PATH"]),
    )
    monitor.authenticate()
    results = monitor.poll()
    log.info("Email monitor: processed %d messages", len(results))
    for r in results:
        log.info("  [%s] %s → %s (company: %s)", r["email_class"], r["subject"][:60], r["status_updated"], r["company_matched"])
