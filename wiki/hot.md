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

**Phase 3 — Testing and Activation** (next)

ACTIVATION PREREQUISITES — system is code-complete but cannot run until:
1. Gmail address — GMAIL_ADDRESS in .env is still placeholder
2. Gmail API credentials — credentials.json does not exist (one-time Google Cloud Console setup)
3. Adzuna API keys — ADZUNA_APP_ID and ADZUNA_API_KEY are placeholders in .env
4. SerpAPI key — SERPAPI_KEY is placeholder in .env

---

## What Is Queued Next

Phase 3 activation steps:
1. Set GMAIL_ADDRESS in .env
2. Google Cloud Console → enable Gmail API → create OAuth2 credentials → download credentials.json
3. Run `python -c "from extensions.email_monitor import EmailMonitor; ..."` → authenticate() flow
4. Obtain Adzuna API keys → add to .env
5. Obtain SerpAPI key → add to .env
6. First live run: `python orchestrator.py --verbose`
7. Add first JD URL to data/pipeline.md, verify full flow end-to-end

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
