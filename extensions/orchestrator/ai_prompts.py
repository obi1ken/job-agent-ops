"""Build prompt text for each AI task kind.

Each builder returns (prompt_text: str, token_estimate: int).
All prompts require Claude Code to emit a machine-readable block:
  <<<RESULT_JSON>>>
  { ... }
  <<<END>>>
so result_handlers can extract structured data without re-reading prose.
"""

from __future__ import annotations

from pathlib import Path

from extensions.interview_prep import PrepBuilder, PrepInput

from .config import ProfileConfig

_RESULT_BLOCK = "<<<RESULT_JSON>>>\n{json_content}\n<<<END>>>"

_SCORE_TEMPLATE = """Score the following job description for Charles Asiegbu across all four tracks.

## Charles's Four Tracks
- Track A — Engineering (AI/Python/autonomous systems)
- Track B — Product & Leadership (PM, Head of AI, delivery)
- Track C — Rail/Civils Digital (digital transformation, COSS/PC background)
- Track D — Document Control (EDMS, Consepsys cert, Aconex/Asite/Procore)

## Scoring Rules
- Score each track 0.0–5.0 in 0.5 increments
- Track D threshold: 3.0 to apply. All others: 3.5
- Track C: score generously where COSS, PC, or Network Rail standards are mentioned
- Track D: detect EDMS platform if mentioned (Aconex, Asite, Procore, Viewpoint, Dalux)
- Select the highest-scoring track as best_track

## Job Description
{jd_text}

---

First, write 2–3 sentences of analysis. Then output exactly:

<<<RESULT_JSON>>>
{{
  "best_track": "A",
  "score": 4.0,
  "scores_all": {{"A": 4.0, "B": 2.5, "C": 1.5, "D": 1.0}},
  "rationale": ["point 1", "point 2", "point 3"],
  "edms_platform": null,
  "above_threshold": true
}}
<<<END>>>
"""

_TAILOR_CV_TEMPLATE = """Tailor Charles Asiegbu's master CV for the following role using Track {track}.

## Role
Company: {company}
Role: {role}
Track: {track}

## Master CV
{master_cv}

## Job Description
{jd_text}

## Track {track} Rules (from modes/_profile.md)
{track_rules}

---

Output the full tailored CV in markdown. Preserve all section headings.
Lead with the Track {track} profile block.
Inject relevant keywords from the JD naturally.
Do not add content that isn't in the master CV.
Never include comment blocks or agent-only notes.

Then output:

<<<RESULT_JSON>>>
{{
  "track": "{track}",
  "keywords_injected": ["kw1", "kw2"],
  "keywords_removed": [],
  "profile_block_used": "Track {track} profile block name"
}}
<<<END>>>
"""

_COVER_LETTER_TEMPLATE = """Write a cover letter for Charles Asiegbu for the following role using Track {track}.

## Role
Company: {company}
Role: {role}
Track: {track}
{edms_line}

## Tailored CV (for context)
{tailored_cv_excerpt}

## Job Description
{jd_text}

## Cover Letter Rules
- Open with one sentence stating the role and why Charles specifically fits it
- Never open with "I am writing to apply"
- Reference {company} by name — show awareness of their work
- One specific achievement as evidence
- Close with clear next step — request for interview
- 1 page max, professional tone
- Track D only: reference EDMS platform in first paragraph if detected

---

Output the full cover letter in plain text. Then output:

<<<RESULT_JSON>>>
{{"word_count": 250, "edms_referenced": false}}
<<<END>>>
"""


def build_score_prompt(
    jd_text: str,
    company: str,
    role: str,
    config: ProfileConfig,
) -> tuple[str, int]:
    jd_truncated = jd_text[:8_000]
    prompt = _SCORE_TEMPLATE.format(jd_text=jd_truncated)
    # Buffer calibrated against the 2026-06-11 live run: real score cost is
    # ~0.6k in+out; 2k buffers made 5 scores jam the 22k window for no reason.
    token_estimate = 500 + len(prompt) // 4
    return prompt, token_estimate


def build_tailor_cv_prompt(
    jd_text: str,
    track: str,
    company: str,
    role: str,
    config: ProfileConfig,
) -> tuple[str, int]:
    master_cv = _read_safe(config.cv_master_path)
    track_rules = _extract_track_rules(config.project_root / "modes" / "_profile.md", track)
    prompt = _TAILOR_CV_TEMPLATE.format(
        track=track,
        company=company,
        role=role,
        master_cv=master_cv[:12_000],
        jd_text=jd_text[:4_000],
        track_rules=track_rules[:2_000],
    )
    token_estimate = 8_000 + len(prompt) // 4
    return prompt, token_estimate


def build_cover_letter_prompt(
    jd_text: str,
    tailored_cv_path: str,
    track: str,
    company: str,
    role: str,
    edms_platform: str | None,
    config: ProfileConfig,
) -> tuple[str, int]:
    tailored_cv = _read_safe(Path(tailored_cv_path))
    edms_line = f"EDMS Platform: {edms_platform}" if edms_platform else ""
    prompt = _COVER_LETTER_TEMPLATE.format(
        track=track,
        company=company,
        role=role,
        edms_line=edms_line,
        tailored_cv_excerpt=tailored_cv[:4_000],
        jd_text=jd_text[:4_000],
    )
    token_estimate = 3_000 + len(prompt) // 4
    return prompt, token_estimate


def build_interview_prep_prompt(
    jd_text: str,
    company: str,
    role: str,
    track: str,
) -> tuple[str, int]:
    prep_input = PrepInput(jd_text=jd_text, company=company, role=role, track=track)
    pkg, _ = PrepBuilder().prepare(prep_input)
    return pkg.task_instructions, pkg.token_estimate


def _read_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return f"[could not read {path}]"


def _extract_track_rules(profile_md_path: Path, track: str) -> str:
    import re
    text = _read_safe(profile_md_path)
    header_map = {"A": "Track A", "B": "Track B", "C": "Track C", "D": "Track D"}
    header = header_map.get(track.upper(), "Track A")
    match = re.search(
        rf"### {re.escape(header)}.*?\n(.*?)(?=^### |\Z)",
        text, re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""
