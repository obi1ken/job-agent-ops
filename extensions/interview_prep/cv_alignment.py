import re
from pathlib import Path
from typing import Optional

from .models import PrepInput

_PROFILE_PATH = "modes/_profile.md"

_PROOF_SECTION_HEADERS = {
    "A": "Track A — Engineering",
    "B": "Track B — Product",
    "C": "Track C — Rail",
    "D": "Track D — Document Control",
}

_PROOF_BLOCK_RE = re.compile(
    r"## Proof Points by Track\n(.*?)(?=^## |\Z)",
    re.MULTILINE | re.DOTALL,
)
_SUBSECTION_RE = re.compile(r"### (.+?)\n(.*?)(?=^### |\Z)", re.MULTILINE | re.DOTALL)
_BULLET_RE = re.compile(r"^- (.+)$", re.MULTILINE)


def get_proof_points(prep_input: PrepInput, max_points: int = 5) -> list[str]:
    path = Path(_PROFILE_PATH)
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")

    proof_block_match = _PROOF_BLOCK_RE.search(text)
    if not proof_block_match:
        return []

    proof_block = proof_block_match.group(1)
    track_key = _PROOF_SECTION_HEADERS.get(prep_input.track.upper(), "Track A — Engineering")

    bullets: list[str] = []
    for match in _SUBSECTION_RE.finditer(proof_block):
        heading = match.group(1).strip()
        if track_key.lower() in heading.lower():
            bullets = _BULLET_RE.findall(match.group(2))
            break

    if not bullets:
        return []

    # Prioritise bullets that mention injected keywords from cv_diff context
    if prep_input.cv_diff and prep_input.cv_diff.keywords_injected:
        keywords = [kw.lower() for kw in prep_input.cv_diff.keywords_injected]
        scored = [(sum(1 for kw in keywords if kw in b.lower()), b) for b in bullets]
        scored.sort(key=lambda x: x[0], reverse=True)
        bullets = [b for _, b in scored]

    return bullets[:max_points]
