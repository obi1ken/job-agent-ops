# hot.md — Rolling Session Context
# Max ~500 words. Updated when Charles says "update hot" or 5+ files written in a session.

Last updated: 2026-04-26 (Phase 2 COMPLETE — all extensions built, orchestrator done)

---

## What Just Shipped

**Phase 2 COMPLETE** — feat/phase-2-discord — PR open, ready to merge.

All 7 extensions + orchestrator built, tested, committed:

| Extension | Commits | Status |
|-----------|---------|--------|
| extensions/notifications/ | 39c0efe | Done |
| extensions/email_monitor/ | d463ae6 | Done |
| extensions/job_discovery/ | 031b050 | Done |
| extensions/cv_diff/ | b0b56e4 | Done |
| extensions/quota_manager/ | 9dd8886 | Done |
| extensions/interview_prep/ | 688417d | Done |
| extensions/deadline_manager/ | 428bba1 | Done |
| orchestrator.py | 3a44f12 | Done |
| requirements.txt | latest | Done |

Key architectural decisions locked in:
- No Anthropic API calls — Claude Code is the AI brain (prompt files in ai_outbox/, outputs in ai_inbox/)
- Exactly-once Discord inbox: offset + message_id dedup, atomic state save
- Human-in-loop non-negotiable: nothing submitted without Charles's Discord approval
- applications.md is read-only for all extensions except email_monitor + submission.py

---

## What Is In Progress

**Phase 3 — First live run** (active)

All 4 activation prerequisites complete as of 2026-04-27:
- AP-1 GMAIL_ADDRESS=miclaud04@gmail.com ✓
- AP-2 credentials.json in place, OAuth consent done ✓
- AP-3 Adzuna keys set ✓
- AP-4 SerpAPI key set ✓

First live run: `python orchestrator.py --verbose`

---

## What Is Queued Next

Phase 3 verification steps:
1. Verify full discovery → score → tailor → cover letter → Discord approval flow
2. Charles approves in Discord → verify submission logs to applications.md
3. Verify GHOST detection (14d) and follow-up scheduler (7d)
4. Verify interview countdown fires 24h before interview date

---

## Open Decisions Carried Forward

OQ-1 LinkedIn URL — placeholder. Update when ready.
OQ-2 Compensation — £45k–£70k assumed. Charles to confirm.
OQ-7 Location for Track C — "Reading UK base, will commute UK-wide" assumed. Confirm.

D2/D3 DATA_CONTRACT tension — always diff CLAUDE.md before running update-system.mjs apply.
D4 applications.md schema vs merge-tracker.mjs — intentional, logged in risks-incidents.md.

Bot details:
- Bot: job-agent-ops-bot | Channel: #job-agent-ops-build | Server: miclaud
- Channel ID: 1497217102531264653 | Charles's user ID: 1379195691624038440
- State dir: C:\Users\obrya\.claude\channels\discord-job-agent-ops\
