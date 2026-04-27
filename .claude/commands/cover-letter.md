# Command: /cover-letter

Generate a track-specific cover letter for a role.

## Usage
/cover-letter [URL or JD text] [optional: track override A/B/C/D]

## What it does
Invokes the cover-letter skill. Requires track to be known (scores JD first if not).
For Track D: runs EDMS detection before writing.

## Output
- Cover letter (track-specific opening, proof point, company reference, interview ask)
- Track D: EDMS platform named in first paragraph
- 1 page max
- Holds for Charles approval
