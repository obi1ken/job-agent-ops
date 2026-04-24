# hot.md — Rolling Session Context
# Max ~500 words. Updated when Charles says "update hot" or 5+ files written in a session.

Last updated: 2026-04-24 (Phase 2 Step 1 complete — bot live, channel ID confirmed)

---

## What Just Shipped

Phase 1 COMPLETE (3 commits on feat/phase-1-foundation). See status.txt for full log.

Phase 2 Step 1 COMPLETE (2026-04-24):
- job-agent-ops-bot live on miclaud server, #job-agent-ops-build
- Channel ID confirmed: 1497217102531264653
- Discord_Bot_Setup_Guide.txt updated: settings.local.json corruption note added,
  job_agent_ops added to active projects list
- status.txt and wiki/hot.md updated to reflect Step 1 complete

---

## What Is In Progress

Phase 2 Step 1 cleanup — commit pending on feat/phase-2-discord:
- Update access.json: replace YOUR_CHANNEL_ID with 1497217102531264653
- Update CLAUDE.md §4: remove "reference only" label, add confirmed channel ID
- Update wiki/pages/discord-integration.md: status planned → current

---

## What Is Queued Next

**Phase 2 Step 2 — build extensions/ folder (after cleanup commit).**

Build order:
1. extensions/notifications/ (Discord client, event types, embed templates) — dependency for all others
2. extensions/email_monitor/ (Gmail API, classifier, tracker updater)
3. extensions/job_discovery/ (Adzuna API + SerpAPI Google Jobs adapters — needs API keys)
4. extensions/cv_diff/ (diff logger + EDMS detection for Track D)
5. extensions/quota_manager/ (5hr rolling window, batch throttle, priority queue)
6. extensions/interview_prep/ (auto-trigger, prep pack generator, Discord delivery)
7. extensions/deadline_manager/ (follow-up scheduler, interview countdown, state machine)
8. orchestrator.py + requirements.txt + .env (gitignored)

Bot details (confirmed):
- Bot: job-agent-ops-bot, channel: #job-agent-ops-build, server: miclaud
- Channel ID: 1497217102531264653
- State dir: C:\Users\obrya\.claude\channels\discord-job-agent-ops\
- Batch file: C:\Users\obrya\start-job-agent-ops.bat
- Charles's Discord user ID: 1379195691624038440

Open decisions still live: OQ-1 (LinkedIn URL), OQ-2 (salary), OQ-5/OQ-6 (API keys), OQ-7 (Track C location).

---

## Open Decisions Carried Forward

D2: CLAUDE.md listed as System Layer in DATA_CONTRACT.md but replaced by Charles-specific content.
    Risk: future update-system.mjs apply may overwrite. Logged in risks-incidents.md.

D3: .claude/skills/* same tension as D2. Logged.

D4: applications.md schema differs from merge-tracker.mjs expectations.
    Intentional — will be superseded by extensions/.

D7: LinkedIn URL still placeholder. Update when LinkedIn profile is ready.
