---
status: current
last_updated: 2026-04-24
last_verified: 2026-04-24
sources:
  - raw/article-digest.md
  - raw/instructions.md
synthesis: End-to-end application pipeline from JD discovery to tracker logging
---

# Application Pipeline

For every job found on any portal:

1. Read full JD carefully
2. Score against all 4 tracks — select highest
3. If Track D: detect EDMS platform before cover letter
4. Generate tailored CV variant
5. Generate matching cover letter (track-specific rules)
6. Run CV diff — log what changed from cv.md master
7. Hold for Charles approval via Discord
8. Submit ONLY after explicit Discord approval
9. Log: platform, company, role, track used, score, date applied
10. Update applications.md via tracker-additions TSV

HUMAN-IN-LOOP RULE: Nothing submits without Charles's explicit approval. Non-negotiable.

## TODO
- [ ] Document TSV format for tracker additions
- [ ] Document CV diff log format (cv_diff extension — Phase 2)
- [ ] Document Discord approval flow (notifications extension — Phase 2)
- [ ] Note: merge-tracker.mjs schema mismatch — see risks-incidents.md
