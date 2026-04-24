---
status: current
last_updated: 2026-04-24
last_verified: 2026-04-24
sources:
  - raw/instructions.md
synthesis: Risk register and incident log for the project
---

# Risks and Incidents

## Risk Register

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|-----------|
| R1 | update-system.mjs overwrites CLAUDE.md (System Layer in DATA_CONTRACT) | Medium | High | Always diff CLAUDE.md before running `node update-system.mjs apply`. Consider adding exclusion to update script in future. |
| R2 | update-system.mjs overwrites .claude/skills/* (System Layer in DATA_CONTRACT) | Medium | Medium | Same as R1. Charles's skill files sit alongside upstream ones. |
| R3 | merge-tracker.mjs breaks on new applications.md schema | High | Low | New schema is intentional per instructions. merge-tracker.mjs will be superseded by extensions/. Do not use merge-tracker.mjs until then. |
| R4 | Upstream modes/ edited accidentally | Low | High | Karpathy principle: Surgical Changes. Never touch upstream without explicit instruction. |
| R5 | Application submitted without Charles approval | Very Low | Very High | HITL rule is non-negotiable. pre-apply.md hook documents this. Phase 2 Discord gate enforces it. |
| R6 | EDMS platform not detected for Track D cover letter | Medium | Medium | EDMS detection is mandatory step in application-pipeline. Documented in _profile.md and cover-letter-rules.md. |

## Incident Log

No incidents recorded.
