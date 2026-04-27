from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SectionDiff:
    section_heading: str
    change_type: str              # "added" | "removed" | "modified" | "unchanged"
    master_text: Optional[str]    # None if added or unchanged
    tailored_text: Optional[str]  # None if removed or unchanged


@dataclass
class DiffEntry:
    # Identity
    timestamp_utc: str
    company: str
    role: str
    track: str                    # "A" | "B" | "C" | "D"

    # Diff payload
    profile_block_used: str
    sections_changed: list[SectionDiff]
    keywords_injected: list[str]  # in tailored, absent from master
    keywords_removed: list[str]   # in master, absent from tailored

    # Word counts
    master_word_count: int
    tailored_word_count: int
    word_count_delta: int

    # EDMS (Track D only — None for A/B/C, empty list means Track D but none found)
    edms_platforms_detected: Optional[list[str]]

    # Linkage to applications.md
    application_ref: dict         # {"company": str, "role": str, "date": str}


@dataclass
class EDMSResult:
    platforms_found: list[str]
    raw_matches: dict = field(default_factory=dict)  # platform_name → list[matched_keywords]
