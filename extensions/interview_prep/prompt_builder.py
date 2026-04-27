from .cv_alignment import get_proof_points
from .models import PrepInput, PromptPackage
from .track_tips import get_track_tips

_JD_MAX_CHARS = 8_000
_BASE_TOKEN_ESTIMATE = 3_000

_TRACK_LABELS: dict[str, str] = {
    "A": "Engineering",
    "B": "Product & Leadership",
    "C": "Rail/Civils Digital",
    "D": "Document Control",
}

_SECTION_NAMES = [
    "Company Research",
    "Role Fit",
    "Likely Questions",
    "Proof Points",
    "Red Flags",
]


def build_prompt(prep_input: PrepInput, research_results: dict | None = None) -> PromptPackage:
    jd_text = prep_input.jd_text[:_JD_MAX_CHARS]
    if len(prep_input.jd_text) > _JD_MAX_CHARS:
        jd_text += "\n[JD truncated at 8,000 characters]"

    track_label = _TRACK_LABELS.get(prep_input.track.upper(), prep_input.track)
    track_tips = get_track_tips(prep_input.track)
    proof_points = get_proof_points(prep_input)

    proof_block = ""
    if proof_points:
        proof_block = "\n## Charles's Proof Points (use these in answers)\n" + "".join(
            f"- {p}\n" for p in proof_points
        )

    diff_block = ""
    if prep_input.cv_diff:
        diff_block = "\n## CV Tailoring Context\n"
        if prep_input.cv_diff.keywords_injected:
            diff_block += f"Keywords injected for this application: {', '.join(prep_input.cv_diff.keywords_injected)}\n"
        if prep_input.cv_diff.keywords_removed:
            diff_block += (
                f"Keywords removed (potential gaps to address): "
                f"{', '.join(prep_input.cv_diff.keywords_removed)}\n"
            )

    research_block = ""
    if research_results:
        research_block = "\n## Web Research Results\n"
        for query, result in research_results.items():
            research_block += f"\n**{query}**\n{result}\n"

    section_instructions = "\n".join(
        f"### {name}\n[Your content here]" for name in _SECTION_NAMES
    )

    instructions = f"""Prepare Charles Asiegbu for a job interview. Generate a structured interview prep pack.

## Role
- Company: {prep_input.company}
- Role: {prep_input.role}
- Track: {prep_input.track} — {track_label}

## Track Guidance
{track_tips}
{proof_block}{diff_block}{research_block}
## Job Description
{jd_text}

---

Output exactly these 5 sections using these exact headings:

### Company Research
2-3 paragraphs: what the company does, current priorities, relevant news or projects. What to reference in the interview to show preparation.

### Role Fit
How Charles's background maps to this specific role. 3-4 concrete alignment points using the proof points above. Be specific — not "Charles has Python experience" but "Charles's MT5 Portfolio Risk Governor demonstrates production-grade Python at scale."

### Likely Questions
8-10 questions this company is likely to ask. Include 2-3 technical, 2-3 behavioural, 1-2 Charles-specific (based on his background). For each question, one-line hint on the best angle to answer from.

### Proof Points
The 3-5 strongest proof points Charles should weave into answers for this specific role. Explain why each one lands for this company — not just what it is.

### Red Flags
2-3 gaps between Charles's background and the JD, areas the interviewer might probe, anything to prepare a pre-emptive response for.
"""

    token_estimate = _BASE_TOKEN_ESTIMATE + len(instructions) // 4
    return PromptPackage(task_instructions=instructions, token_estimate=token_estimate)
