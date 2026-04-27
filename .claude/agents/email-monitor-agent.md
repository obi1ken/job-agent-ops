# Agent: Email Monitor Agent

## Purpose
Subagent responsible for monitoring Gmail for inbound employer responses
and classifying them. Phase 2 only.

## Tools
Read, Write, Bash (for email API calls)

## Inputs
- Inbound emails from Charles's Gmail account (address in .env as GMAIL_ADDRESS)
- data/applications.md (match emails to tracked applications)

## Outputs
- Classification: INTERVIEW_INVITE / RECRUITER_REPLY / AUTO_REJECTION / GHOST / OFFER
- TSV entry in batch/tracker-additions/ to update application status
- Discord notification (via notifications extension) for INTERVIEW_INVITE and OFFER

## Constraints
- Phase 2 only — not operational until email_monitor extension is built
- Email platform is Gmail — uses Gmail API (OAuth credentials in .env)
- GHOST classification triggers only after 7+ days of no response
- AUTO_REJECTION: update tracker and log; no Discord notification needed
- OFFER: urgent Discord notification required immediately
