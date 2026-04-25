import re
from datetime import datetime, timezone

from .models import PrepResult, PrepSection

_SECTION_NAMES = [
    "Company Research",
    "Role Fit",
    "Likely Questions",
    "Proof Points",
    "Red Flags",
]

_SECTION_PATTERN = re.compile(
    r"###\s+(" + "|".join(re.escape(n) for n in _SECTION_NAMES) + r")\s*\n(.*?)(?=###\s+(?:"
    + "|".join(re.escape(n) for n in _SECTION_NAMES)
    + r")|\Z)",
    re.DOTALL,
)
_ORDER = {name: i for i, name in enumerate(_SECTION_NAMES)}


def parse_response(raw: str, company: str, role: str, track: str) -> PrepResult:
    sections: list[PrepSection] = []
    found: set[str] = set()

    for match in _SECTION_PATTERN.finditer(raw):
        name = match.group(1).strip()
        content = match.group(2).strip()
        sections.append(PrepSection(name=name, content=content))
        found.add(name)

    for name in _SECTION_NAMES:
        if name not in found:
            sections.append(PrepSection(name=name, content="[Section not generated]"))

    sections.sort(key=lambda s: _ORDER.get(s.name, 99))

    return PrepResult(
        company=company,
        role=role,
        track=track,
        sections=sections,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )
