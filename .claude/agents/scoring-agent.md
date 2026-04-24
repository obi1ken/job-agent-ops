# Agent: Scoring Agent

## Purpose
Subagent responsible for scoring job descriptions against all 4 tracks and
selecting the best-fit variant.

## Tools
Read, Write, WebSearch, WebFetch

## Inputs
- JD text or URL
- modes/_profile.md (track scoring criteria)
- modes/_shared.md (base scoring system, blocks A-F + G)
- config/profile.yml (thresholds)

## Outputs
- Score report in reports/ (format: {###}-{company-slug}-{YYYY-MM-DD}.md)
- TSV entry in batch/tracker-additions/ for merge-tracker.mjs
- Selected track and score returned to orchestrator

## Constraints
- Never fabricate scores or metrics
- Always score all 4 tracks; never assume from portal source alone
- Track C: apply 0.5 boost where COSS/PC/possession/Sentinel mentioned
- Track D: trigger EDMS detection flag if score ≥ 3.0
- Always register in tracker after scoring
