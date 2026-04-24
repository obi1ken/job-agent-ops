---
status: current
last_updated: 2026-04-24
last_verified: 2026-04-24
sources:
  - raw/article-digest.md
  - raw/instructions.md
synthesis: 4-variant auto-track selection, per-track score thresholds, and archetype detection rules
---

# Scoring Logic

Score every JD against all four tracks. Select highest. See modes/_profile.md for full logic.

| Threshold | Action |
|-----------|--------|
| < 3.0 | Never apply |
| 3.0–3.4 | Track D only (Consepsys cert match) |
| 3.5–3.9 | Apply (all tracks except D if below 3.5) |
| 4.0–4.4 | Priority flag |
| 4.5+ | Urgent — Discord ping (Phase 2) |

Track C: score generously where COSS/PC mentioned. Combination is rare.

## TODO
- [ ] Expand archetype detection signals (new archetypes: Rail, Non-SW Eng, Ops, Doc Control)
- [ ] Document tie-breaking rule (portal source preference)
- [ ] Document Track D EDMS detection trigger
- [ ] Document Block G legitimacy assessment (from upstream _shared.md)
