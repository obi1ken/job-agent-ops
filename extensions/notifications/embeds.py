from datetime import datetime, timezone
from .events import JobEvent

_COLORS = {
    JobEvent.JOB_FOUND:        0x3498DB,  # blue
    JobEvent.CV_READY:         0x2ECC71,  # green
    JobEvent.REPLY_RECEIVED:   0xF1C40F,  # yellow
    JobEvent.INTERVIEW_INVITE: 0xE67E22,  # orange
    JobEvent.REJECTION:        0xE74C3C,  # red
    JobEvent.OFFER:            0xF39C12,  # gold
    JobEvent.GHOST:            0x95A5A6,  # grey
}

_TITLES = {
    JobEvent.JOB_FOUND:        "Job Found",
    JobEvent.CV_READY:         "CV Ready for Review",
    JobEvent.REPLY_RECEIVED:   "Email Reply Received",
    JobEvent.INTERVIEW_INVITE: "Interview Invite",
    JobEvent.REJECTION:        "Rejection",
    JobEvent.OFFER:            "Job Offer",
    JobEvent.GHOST:            "No Response — 7 Days",
}


def _field(name: str, value: str, inline: bool = True) -> dict:
    return {"name": name, "value": str(value), "inline": inline}


def build_embed(event: JobEvent, **kwargs) -> dict:
    fields = []

    for key, label in [("company", "Company"), ("role", "Role"), ("track", "Track")]:
        if kwargs.get(key):
            fields.append(_field(label, kwargs[key]))
    if kwargs.get("score") is not None:
        fields.append(_field("Score", f"{kwargs['score']}/5"))

    if event == JobEvent.JOB_FOUND:
        if kwargs.get("portal"):
            fields.append(_field("Portal", kwargs["portal"]))
        if kwargs.get("url"):
            fields.append(_field("URL", kwargs["url"], inline=False))

    elif event == JobEvent.CV_READY:
        if kwargs.get("cv_path"):
            fields.append(_field("CV File", kwargs["cv_path"], inline=False))

    elif event == JobEvent.REPLY_RECEIVED:
        if kwargs.get("subject"):
            fields.append(_field("Subject", kwargs["subject"], inline=False))
        if kwargs.get("classifier"):
            fields.append(_field("Classifier", kwargs["classifier"]))

    elif event == JobEvent.INTERVIEW_INVITE:
        if kwargs.get("date"):
            fields.append(_field("Date", kwargs["date"]))
        if kwargs.get("location"):
            fields.append(_field("Location", kwargs["location"]))

    elif event == JobEvent.OFFER:
        if kwargs.get("salary"):
            fields.append(_field("Salary", kwargs["salary"]))
        if kwargs.get("start_date"):
            fields.append(_field("Start Date", kwargs["start_date"]))

    elif event == JobEvent.GHOST:
        if kwargs.get("days"):
            fields.append(_field("Days Since Applied", str(kwargs["days"])))

    return {
        "title": _TITLES[event],
        "color": _COLORS[event],
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "job-agent-ops"},
    }
