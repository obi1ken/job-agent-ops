---
status: planned
last_updated: 2026-04-24
last_verified: 2026-04-24
sources:
  - raw/article-digest.md
  - raw/instructions.md
synthesis: Gmail polling, inbound response classification, and tracker state updates (Phase 2)
---

# Email Monitor

**STATUS: PLANNED — Phase 2 only. Not yet configured.**

Monitors Gmail account for inbound employer responses (job applications use Gmail).

Classification taxonomy:
- INTERVIEW_INVITE → trigger interview prep workflow
- RECRUITER_REPLY → notify Discord, await Charles instruction
- AUTO_REJECTION → update tracker, log, no Discord notification
- GHOST (no response 7+ days) → nudge Charles via Discord to follow up
- OFFER → urgent Discord notification, flag for immediate attention

## TODO
- [ ] Document Gmail API setup (OAuth credentials in .env)
- [ ] Document polling interval
- [ ] Document classifier prompt (Claude classifies each inbound)
- [ ] Document tracker_updater.py state machine
- [ ] Gmail API confirmed — OAuth credentials in .env (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
