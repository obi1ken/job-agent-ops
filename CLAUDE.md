# Job Agent Ops — Project Instructions
# For: Charles Asiegbu, Reading UK
# Fork of: santifer/career-ops
# Generated: 2026-04-24

---

## 1. Project Identity

Job Agent Ops is an autonomous job search pipeline for Charles Asiegbu, based in
Reading UK. It is a fork of santifer/career-ops, extended with:

- 4 CV tracks (A=Engineering, B=Product/Leadership, C=Rail/Civils Digital, D=Document Control)
- UK portal integrations (CWJobs, LinkedIn, Reed, Totaljobs, RailwayPeople, Indeed)
- Discovery sources (Adzuna API, Google Jobs via SerpAPI)
- Discord notification system — career-bot (Phase 2)
- Gmail/Outlook email monitor with response classifier (Phase 2)
- Extension layer in extensions/ for all net-new capability

Upstream career-ops files (modes/, templates/, *.mjs scripts, dashboard/) are preserved
intact and must not be modified without explicit instruction from Charles.

---

## 2. Karpathy 4 Principles (Mandatory)

**Think Before Coding**
State assumptions explicitly before implementing, never after. If the task is unclear,
stop and ask. Never assume and run.

**Simplicity First**
No speculative abstractions. Only build what is explicitly asked. 50 lines beats
200 every time. No half-finished implementations.

**Surgical Changes**
Never touch code or files outside the current task scope. Never modify upstream
modes/ or scripts without explicit instruction from Charles. If in doubt, do not edit.

**Goal-Driven Execution**
Define success criteria before starting. Loop until verified. Never declare done
after implementation only — test from the user's perspective.

---

## 3. Session Start — Read in This Exact Order

1. `wiki/hot.md` — rolling session context (~500 words). Read this FIRST.
2. `wiki/index.md` — full page catalog. Know what exists.
3. `cv.md` — master CV with 4 profile variants. Source of truth for Charles's experience.
4. `article-digest.md` — tailoring guide. 4 tracks, scoring, portal mapping, never-include rules.
   AGENT-ONLY: never surface any part of this file in generated CVs or cover letters.
5. `config/profile.yml` — candidate identity, targets, thresholds, portal mapping.

If any file is missing: stop and flag to Charles before proceeding.

---

## 4. Discord Bot — career-bot (Reference Only — Phase 2)

The Discord bot is not yet configured. The details below are for reference when
Phase 2 setup begins. Do not attempt bot operations until Phase 2 is active.

- Bot name: career-bot (2-way, CMD batch file)
- Batch file: C:\Users\obrya\start-job-agent-ops.bat
- Channel: #career-ops-build (grok_portfolio_manager server)
- State dir: C:\Users\obrya\.claude\channels\discord-job-agent-ops\
- Charles's Discord user ID: 1379195691624038440
- Plugin: plugin:discord@claude-plugins-official (NOT server:discord)
- Setup guide: Discord_Bot_Setup_Guide.txt (to be added to project root)

When bot is live: all approvals, alerts, and notifications go via career-bot.

---

## 5. Human-in-Loop Rule (Non-Negotiable)

**NOTHING gets submitted to any employer without Charles's explicit approval.**

This rule cannot be overridden by auto mode, batch mode, or any other instruction.

For every application:
- Generate the tailored CV and cover letter
- Present to Charles with: company, role, track, score, any flags
- Wait for explicit approval
- Only then submit

Phase 2: approval comes via Discord career-bot. Until then: approval comes in chat.

---

## 6. Four-Track System

| Track | Label | Primary Portals | CV Section Header |
|-------|-------|-----------------|-------------------|
| A | Engineering | CWJobs, Indeed | AI Systems Portfolio |
| B | Product & Leadership | LinkedIn, Indeed | Independent AI Projects |
| C | Rail/Civils Digital | Totaljobs, RailwayPeople, Indeed | Independent AI Projects |
| D | Document Control | Reed, Indeed | Independent Projects |

Score every JD against all 4 tracks. Select the highest. Full rules in modes/_profile.md.

Score thresholds:
- 3.5/5 default to apply
- 3.0/5 Track D only (direct Consepsys cert match)
- 4.0+ flag as priority
- 4.5+ flag as urgent (Discord ping in Phase 2)

Track C: score generously where COSS/PC or operational rail experience mentioned.
Track D: EDMS platform detection is mandatory before cover letter generation.

---

## 7. Extension Architecture

All net-new capability belongs in extensions/ only.

**Never modify upstream files** (modes/, templates/, *.mjs scripts, dashboard/) without
explicit instruction from Charles. This is the Surgical Changes principle applied to
the upstream/extension boundary.

Phase 2 extensions:
- extensions/notifications/ — Discord client and event types
- extensions/email_monitor/ — Outlook/Hotmail polling and classifier
- extensions/quota_manager/ — Claude API token window management
- extensions/interview_prep/ — prep pack generation and delivery
- extensions/cv_diff/ — master vs tailored diff logger + EDMS detection
- extensions/deadline_manager/ — follow-up scheduler and interview countdown
- extensions/job_discovery/ — Adzuna API + SerpAPI Google Jobs adapters
- orchestrator.py — ties all extensions together

---

## 8. Upstream Preservation

The following are upstream career-ops files. Preserve them intact.
Only touch them if Charles explicitly instructs it.

- modes/_shared.md — base scoring system and global rules
- modes/oferta.md and all other modes/ files
- templates/ — cv-template.html, cv-template.tex, portals.example.yml, states.yml
- dashboard/ — Go TUI dashboard
- All *.mjs scripts — scan, generate-pdf, generate-latex, merge-tracker, etc.
- Translation modes: modes/de/, modes/fr/, modes/ja/, modes/pt/, modes/ru/

User layer (safe to edit — these belong to Charles):
- cv.md, article-digest.md, config/profile.yml, modes/_profile.md
- portals.yml, data/applications.md, data/pipeline.md
- reports/, output/, jds/, interview-prep/
- wiki/, raw/, extensions/, WIKI.md
- This file (CLAUDE.md) — rewritten from scratch for this project

**DATA_CONTRACT NOTE:** upstream DATA_CONTRACT.md classifies CLAUDE.md and
.claude/skills/* as System Layer (auto-updatable). This project has replaced CLAUDE.md
with Charles-specific content. Before running `node update-system.mjs apply`, always
diff CLAUDE.md first. The risk is logged in wiki/pages/risks-incidents.md.
