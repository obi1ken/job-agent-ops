from enum import Enum


class JobEvent(str, Enum):
    JOB_FOUND = "JOB_FOUND"
    CV_READY = "CV_READY"
    REPLY_RECEIVED = "REPLY_RECEIVED"
    INTERVIEW_INVITE = "INTERVIEW_INVITE"
    REJECTION = "REJECTION"
    OFFER = "OFFER"
    GHOST = "GHOST"


# These events trigger an @mention — Charles must see them immediately
URGENT_EVENTS = {JobEvent.INTERVIEW_INVITE, JobEvent.OFFER, JobEvent.GHOST}
