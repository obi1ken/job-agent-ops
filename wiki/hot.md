# hot.md — Rolling Session Context
# Max ~500 words. Updated when Charles says "update hot" or 5+ files written in a session.

Last updated: 2026-04-24 (commit 3 — naming corrections)

---

## What Just Shipped

Phase 1 is FULLY COMPLETE. Three commits on feat/phase-1-foundation.

Commit 1 — Phase 1 foundation:
- config/profile.yml, modes/_profile.md, portals.yml
- data/applications.md, data/pipeline.md
- WIKI.md, raw/, wiki/ (hot/index/log), wiki/pages/ (13 stubs)
- .claude/skills/ (4), commands/ (5), agents/ (6), hooks/ (2), settings.json
- CLAUDE.md — full 8-section rewrite
- Discord_Bot_Setup_Guide.txt committed

Commit 2 — Gmail and bot name corrections:
- email-monitor-agent.md, wiki/pages/email-monitor.md: Hotmail → Gmail
- OQ-3 marked resolved (Gmail confirmed for job applications)
- OQ-4 resolved (Discord_Bot_Setup_Guide.txt now in project)

Commit 3 — Naming corrections (current):
- All career-bot → job-agent-ops-bot
- All #career-ops-build → #job-agent-ops-build
- Server reference → miclaud
- Removed all "career-ops" from project-layer files (upstream untouched)
- Gmail API confirmed throughout email_monitor references

---

## What Is In Progress

Nothing. Phase 1 is done. Phase 2 ready to begin.

---

## What Is Queued Next

**Phase 2 — new session required.**

Phase 2 sequence:
1. Discord bot setup (job-agent-ops-bot via plugin:discord@claude-plugins-official)
   - State dir: C:\Users\obrya\.claude\channels\discord-job-agent-ops\
   - Batch file: C:\Users\obrya\start-job-agent-ops.bat
   - Channel: #job-agent-ops-build on miclaud server
   - Charles's Discord user ID: 1379195691624038440
   - Discord_Bot_Setup_Guide.txt is in project root — refer to it for full setup procedure
2. Update CLAUDE.md Discord section from "reference only" to confirmed bot details
3. Build extensions/ folder:
   - extensions/notifications/ (Discord client, event types, embed templates)
   - extensions/email_monitor/ (Gmail API, classifier, tracker updater)
   - extensions/quota_manager/ (5hr rolling window, batch throttle, priority queue)
   - extensions/interview_prep/ (auto-trigger, prep pack generator, Discord delivery)
   - extensions/cv_diff/ (master vs tailored diff, EDMS detection for Track D)
   - extensions/deadline_manager/ (follow-up scheduler, interview countdown, state machine)
   - extensions/job_discovery/ (Adzuna API + SerpAPI Google Jobs adapters)
   - orchestrator.py (ties all extensions)
   - requirements.txt
   - .env (gitignored)

---

## Open Decisions Carried Forward

D2: CLAUDE.md listed as System Layer in DATA_CONTRACT.md but replaced by Item C.
    Risk: future update-system.mjs apply may overwrite. Logged in risks-incidents.md.

D3: .claude/skills/* same tension as D2. Logged.

D4: applications.md schema differs from merge-tracker.mjs expectations.
    merge-tracker.mjs not modified (upstream). Will be superseded by extensions.

D7: LinkedIn URL still placeholder. Update when LinkedIn profile is ready.
