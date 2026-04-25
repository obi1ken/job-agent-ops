import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import DiffEntry, EDMSResult, SectionDiff

_SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_WORD_RE = re.compile(r"\b\w+\b")
_TRUNCATE = 500


class CvDiffer:
    def __init__(self, master_cv_path: str):
        text = Path(master_cv_path).read_text(encoding="utf-8")
        self._master_text = text
        self._master_sections = _parse_sections(text)

    def compute_diff(
        self,
        tailored_md: str,
        track: str,
        jd_keywords: list[str],
        company: str,
        role: str,
        edms_result: Optional[EDMSResult] = None,
    ) -> DiffEntry:
        tailored_sections = _parse_sections(tailored_md)

        all_headings = set(self._master_sections) | set(tailored_sections)
        sections_changed: list[SectionDiff] = []

        for heading in sorted(all_headings):
            master_body = self._master_sections.get(heading)
            tailored_body = tailored_sections.get(heading)

            if master_body is None:
                change_type = "added"
            elif tailored_body is None:
                change_type = "removed"
            elif master_body.strip() != tailored_body.strip():
                change_type = "modified"
            else:
                change_type = "unchanged"

            sections_changed.append(SectionDiff(
                section_heading=heading,
                change_type=change_type,
                master_text=_trunc(master_body) if change_type != "unchanged" else None,
                tailored_text=_trunc(tailored_body) if change_type != "unchanged" else None,
            ))

        profile_block = _detect_profile_block(tailored_sections, track)

        return DiffEntry(
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            company=company,
            role=role,
            track=track,
            application_ref={
                "company": company,
                "role": role,
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            },
            profile_block_used=profile_block,
            sections_changed=sections_changed,
            keywords_injected=self._find_injected_keywords(jd_keywords, tailored_md),
            keywords_removed=self._find_removed_keywords(jd_keywords, tailored_md),
            master_word_count=_count_words(self._master_text),
            tailored_word_count=_count_words(tailored_md),
            word_count_delta=_count_words(tailored_md) - _count_words(self._master_text),
            edms_platforms_detected=edms_result.platforms_found if edms_result is not None else None,
        )

    def _find_injected_keywords(self, jd_keywords: list[str], tailored_md: str) -> list[str]:
        """Keywords in JD present in tailored but absent from master."""
        master_lower = self._master_text.lower()
        tailored_lower = tailored_md.lower()
        return [kw for kw in jd_keywords if kw.lower() not in master_lower and kw.lower() in tailored_lower]

    def _find_removed_keywords(self, jd_keywords: list[str], tailored_md: str) -> list[str]:
        """Keywords present in master but absent from tailored — catches accidental drops."""
        master_lower = self._master_text.lower()
        tailored_lower = tailored_md.lower()
        return [kw for kw in jd_keywords if kw.lower() in master_lower and kw.lower() not in tailored_lower]


def _parse_sections(md_text: str) -> dict[str, str]:
    headings = list(_SECTION_RE.finditer(md_text))
    sections: dict[str, str] = {}
    for i, match in enumerate(headings):
        heading = match.group(1).strip()
        start = match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(md_text)
        sections[heading] = md_text[start:end].strip()
    return sections


def _count_words(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _trunc(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    return text[:_TRUNCATE] + "…" if len(text) > _TRUNCATE else text


def _detect_profile_block(sections: dict[str, str], track: str) -> str:
    _track_keywords = {
        "A": "engineering focus",
        "B": "product",
        "C": "rail",
        "D": "document control",
    }
    keyword = _track_keywords.get(track, "")
    for heading in sections:
        if keyword and keyword in heading.lower():
            return heading
    return next(iter(sections), "Unknown")
