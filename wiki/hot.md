# hot.md — Rolling Session Context
# Max ~500 words. Updated when Charles says "update hot" or 5+ files written in a session.

Last updated: 2026-06-11 (pipeline reset — repo cleanup, fresh Phase 3 restart queued)

---

## What Just Shipped

All fixes are in main as of 2026-06-01:
- PR #2 (post-merge-bugfixes): email monitor notify filter, GMAIL_LABEL, per-track
  search queries, quota heap fix, JD filename sanitisation (Windows colons)
- PR #3 (fix/phase3-pipeline-bugs): quota prune, queue persistence, approval msg ID

2026-06-11 repo cleanup (chore/repo-cleanup):
- Deleted jds/serpapi — 0-byte NTFS-stream debris from the pre-fix colon bug
- Deleted 23 orphaned ai_outbox prompt files (all tasks complete/failed)
- deadline_state.json now gitignored (was the only tracked runtime state file)
- hot.md refreshed from stale stash

---

## What Is In Progress

**Phase 3 RESTART** — Charles cancelled all in-flight jobs on 2026-06-11.

The 2026-06-01 first live run worked end-to-end EXCEPT approvals never reached
Discord (discord_message_id null — the exact bug PR #3 fixed 30 min before
shutdown). The fix has never been live-tested.

Cancelled on restart: S&P Global Track B 4.0 + IRIS OS Track A 4.5 approvals
(both REJECTED), Swiss Re SCORE_JD task (FAILED/cancelled).

Next: fresh `python orchestrator.py --verbose` run to verify the full
discovery → score → tailor → cover letter → Discord approval flow.

---

## What Is Queued Next

Phase 3 verification steps (unchanged):
1. Verify discovery finds real jobs via Adzuna + SerpAPI
2. Verify scoring selects correct track per JD
3. Verify tailored CV + cover letter generation
4. **Verify approval message actually lands in Discord (the untested PR #3 fix)**
5. Charles approves in Discord → verify submission logs to applications.md
6. Verify GHOST detection (14d) and follow-up scheduler (7d)
7. Verify interview countdown fires 24h before interview date

---

## Open Decisions Carried Forward

OQ-1 LinkedIn URL — placeholder. Update when ready.
OQ-2 Compensation — £45k–£70k assumed. Charles to confirm.
OQ-7 Location for Track C — "Reading UK base, will commute UK-wide" assumed. Confirm.

NEW: Mistral AI discrepancy — applications.md says "Approved — Pending Manual
Submission" (2026-04-28) but deadline_state.json registered it APPLIED on
2026-06-01. Charles to confirm whether it was actually submitted.

D2/D3 DATA_CONTRACT tension — always diff CLAUDE.md before running update-system.mjs apply.
D4 applications.md schema vs merge-tracker.mjs — intentional, logged in risks-incidents.md.

Bot details:
- Bot: job-agent-ops-bot | Channel: #job-agent-ops-build | Server: miclaud
- Channel ID: 1497217102531264653 | Charles's user ID: 1379195691624038440
- State dir: C:\Users\obrya\.claude\channels\discord-job-agent-ops\
