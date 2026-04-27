# Skill: Job Scoring

## Purpose
Score a job description against all 4 CV tracks and select the best-fit variant.

## When to invoke
Any time a JD or job URL is provided for evaluation.

## How to apply
1. Read the full JD carefully
2. Read modes/_profile.md for track scoring criteria and archetype detection
3. Read modes/_shared.md for base scoring system (blocks A-F + legitimacy block G)
4. Score the JD independently against all 4 tracks
5. Use archetype detection signals (both upstream archetypes and new Tracks C/D archetypes)
6. Track C: boost score by 0.5 if COSS, PC, SSOW, or possession language present
7. Track D: trigger EDMS detection if score ≥ 3.0
8. Select the highest-scoring track. On tie: prefer track matching source portal
9. Apply score thresholds: 3.5 default, 3.0 Track D, 4.0 priority, 4.5 urgent
10. State selected track and reasoning at top of report
11. Register in applications.md via batch/tracker-additions/ TSV (never edit directly)
