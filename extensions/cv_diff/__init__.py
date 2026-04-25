import os
from typing import Optional

from .differ import CvDiffer
from .edms_detector import EDMSDetector, EDMSNotDetectedWarning
from .log_writer import DiffLogWriter
from .models import DiffEntry, EDMSResult, SectionDiff

__all__ = [
    "CvDiffer", "EDMSDetector", "EDMSNotDetectedWarning",
    "DiffLogWriter", "DiffEntry", "EDMSResult", "SectionDiff",
    "run_diff",
]

_DEFAULT_CV_PATH = "cv.md"
_DEFAULT_LOG_PATH = "output/cv_diff_log.jsonl"


def run_diff(
    tailored_md: str,
    track: str,
    jd_keywords: list[str],
    company: str,
    role: str,
    jd_text: str = "",
    master_cv_path: Optional[str] = None,
    log_path: Optional[str] = None,
) -> DiffEntry:
    cv_path = master_cv_path or os.environ.get("CV_MASTER_PATH", _DEFAULT_CV_PATH)
    out_path = log_path or os.environ.get("CV_DIFF_LOG_PATH", _DEFAULT_LOG_PATH)

    edms_result: Optional[EDMSResult] = None
    if track == "D" and jd_text:
        edms_result = EDMSDetector().detect_for_track_d(jd_text, company, role)

    entry = CvDiffer(cv_path).compute_diff(
        tailored_md=tailored_md,
        track=track,
        jd_keywords=jd_keywords,
        company=company,
        role=role,
        edms_result=edms_result,
    )

    DiffLogWriter(out_path).append(entry)
    return entry
