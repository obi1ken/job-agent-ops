# hot.md — Rolling Session Context
# Max ~500 words. Updated when Charles says "update hot" or 5+ files written in a session.

Last updated: 2026-04-24

---

## What Just Shipped

Phase 1 foundation is complete. All onboarding and scaffold files written in one session.

Files created:
- config/profile.yml — Charles's full profile, 4 tracks, thresholds, portal mapping
- modes/_profile.md — canonical 4-track rules, proof points, archetypes, never-include rules
- portals.yml — UK-curated scanner config (6 profile portals + Adzuna/SerpAPI + 20 tracked companies)
- data/applications.md — tracker initialised (empty, correct headers)
- data/pipeline.md — URL inbox initialised (empty, ready to receive)
- WIKI.md — wiki schema and governance rules
- raw/ — seeded with cv.md, article-digest.md, instructions.md
- wiki/ — hot.md, index.md, log.md
- wiki/pages/ — 13 stub pages (approved skeleton)
- .claude/skills/ — 4 skill files
- .claude/commands/ — 5 command files
- .claude/agents/ — 6 agent files
- .claude/hooks/ — 2 hook files (.md only, no .sh)
- .claude/settings.json
- CLAUDE.md — full rewrite per 8-section spec

---

## What Is In Progress

Nothing. Phase 1 is done.

---

## What Is Queued Next

**Phase 2 — new session required.**

Phase 2 sequence:
1. Discord bot setup (career-bot via plugin:discord@claude-plugins-official)
   - State dir: C:\Users\obrya\.claude\channels\discord-job-agent-ops\
   - Batch file: C:\Users\obrya\start-job-agent-ops.bat
   - Channel: #career-ops-build on grok_portfolio_manager server
   - Charles's Discord user ID: 1379195691624038440
   - NOTE: Discord_Bot_Setup_Guide.txt not yet in project — Charles to add or provide details
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
