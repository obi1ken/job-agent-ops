---
status: current
last_updated: 2026-04-24
last_verified: 2026-04-24
sources:
  - raw/article-digest.md
synthesis: Interview prep trigger conditions and prep pack generation workflow
---

# Interview Prep Workflow

Triggered when INTERVIEW_INVITE is detected (email monitor — Phase 2).

Steps:
1. Pull original JD used for application
2. Pull CV version submitted
3. Research company (recent news, projects, tech stack)
4. Generate likely interview questions from JD + CV variant
5. Generate model answers using Charles's actual experience
6. Generate company brief (key facts, recent projects, interviewers if known)
7. Deliver prep pack to Discord (formatted message + PDF)
8. Set 24-hour reminder before interview via Discord

## TODO
- [ ] Link to email-monitor.md for INTERVIEW_INVITE classification
- [ ] Document prep pack PDF template
- [ ] Document Discord delivery format (Phase 2)
- [ ] Document 24hr reminder mechanism (deadline_manager extension)
