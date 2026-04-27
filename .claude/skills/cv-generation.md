# Skill: CV Generation

## Purpose
Generate a tailored CV variant for a specific job, selecting the correct track profile
and injecting JD keywords while respecting all never-include rules.

## When to invoke
User says "generate CV", "tailor CV", "create CV for this role", or a JD has been scored
and track selected.

## How to apply
1. Read cv.md — the canonical master CV
2. Read modes/_profile.md — track rules, lead-with bullets, de-emphasise rules, never-include list
3. Read article-digest.md — proof points (takes precedence over cv.md for metrics)
4. Identify which track was selected (A/B/C/D)
5. Select the correct profile block from cv.md
6. Apply lead-with and de-emphasise rules for the track
7. Inject keywords from the JD (listed per track in _profile.md)
8. Strip all comment blocks from cv.md (the `<!-- USE FOR -->` blocks)
9. Apply the correct CV section header for the track
10. Never include anything from article-digest.md verbatim
11. Run CV diff before finalising — log what changed from master
12. Hold for Charles approval. Never submit.
