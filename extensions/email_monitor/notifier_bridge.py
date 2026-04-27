from extensions.notifications import DiscordNotifier, JobEvent
from .classifier import EmailClass


class DiscordNotificationError(Exception):
    pass


def dispatch_notification(
    email_class: EmailClass,
    company: str,
    role: str,
    subject: str,
    email_date: str,
) -> None:
    notifier = DiscordNotifier()
    common = {"company": company, "role": role}

    try:
        if email_class == EmailClass.INTERVIEW_INVITE:
            notifier.send(JobEvent.REPLY_RECEIVED, subject=subject, classifier="INTERVIEW_INVITE", **common)
            notifier.send(JobEvent.INTERVIEW_INVITE, **common)  # @mention — date/location unknown at this stage
        elif email_class == EmailClass.REJECTION:
            notifier.send(JobEvent.REJECTION, **common)
        elif email_class == EmailClass.OFFER:
            notifier.send(JobEvent.OFFER, **common)  # @mention
        elif email_class == EmailClass.INFO_REQUEST:
            notifier.send(JobEvent.REPLY_RECEIVED, subject=subject, classifier="INFO_REQUEST", **common)
        else:
            notifier.send(JobEvent.REPLY_RECEIVED, subject=subject, classifier="UNKNOWN", **common)
    except Exception as exc:
        raise DiscordNotificationError(str(exc)) from exc
