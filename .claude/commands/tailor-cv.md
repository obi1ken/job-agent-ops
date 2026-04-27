# Command: /tailor-cv

Generate a tailored CV variant for a specific job.

## Usage
/tailor-cv [URL or JD text] [optional: track override A/B/C/D]

## What it does
Invokes the cv-generation skill. Scores the JD first if not already scored,
selects track, generates tailored variant, logs CV diff, holds for approval.

## Output
- Selected track and rationale
- Tailored CV (correct profile block, keywords injected, de-emphasise rules applied)
- CV diff summary (what changed from cv.md master)
- Cover letter (always generated alongside CV)
- Awaits Charles approval before any submission
