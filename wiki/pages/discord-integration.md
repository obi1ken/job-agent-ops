---
status: current
last_updated: 2026-04-24
last_verified: 2026-04-24
sources:
  - raw/instructions.md
synthesis: Discord job-agent-ops-bot setup parameters and step-by-step procedure from Discord_Bot_Setup_Guide.txt (Phase 2)
---

# Discord Integration

**STATUS: CURRENT — Bot live as of 2026-04-24.**

Setup guide: `Discord_Bot_Setup_Guide.txt` (project root) — full procedure with troubleshooting.

## Parameters

| Item | Value |
|------|-------|
| Bot name | job-agent-ops-bot |
| Channel | #job-agent-ops-build |
| Server | miclaud |
| Channel ID (incoming chat_id) | 1497217102531264653 |
| access.json channel ID | 1497197893260415146 |
| Charles's Discord user ID | 1379195691624038440 |
| State dir | `C:\Users\obrya\.claude\channels\discord-job-agent-ops\` |
| Batch file | `C:\Users\obrya\start-job-agent-ops.bat` |
| Plugin | `plugin:discord@claude-plugins-official` (NOT `server:discord`) |

## Files to create in state dir

```
C:\Users\obrya\.claude\channels\discord-job-agent-ops\
  .env          DISCORD_BOT_TOKEN=<token>
                DISCORD_STATE_DIR=C:\Users\obrya\.claude\channels\discord-job-agent-ops
  access.json   dmPolicy, allowFrom (Charles's user ID), groups (channel ID)
  approved\     (empty directory — required)
```

## access.json template

```json
{
  "dmPolicy": "allowlist",
  "allowFrom": ["1379195691624038440"],
  "groups": {
    "YOUR_CHANNEL_ID": {
      "requireMention": false,
      "allowFrom": []
    }
  },
  "pending": {}
}
```

## Batch file template

```bat
@echo off
set DISCORD_BOT_TOKEN=YOUR_FULL_BOT_TOKEN
set DISCORD_STATE_DIR=C:\Users\obrya\.claude\channels\discord-job-agent-ops
cd C:\Users\obrya\Documents\job_agent_ops
claude --channels plugin:discord@claude-plugins-official
```

## Setup sequence (from Discord_Bot_Setup_Guide.txt)

1. Discord Developer Portal → New Application → name it `job-agent-ops-bot`
2. Bot section → username `job-agent-ops-bot` → Reset Token → copy token (shown once only)
3. Privileged Gateway Intents → enable ALL THREE (Presence, Server Members, Message Content)
4. OAuth2 URL Generator → Scopes: bot → Permissions: Send Messages, Read Messages, Read Message History → invite to server
5. Discord server (miclaud) → create `#job-agent-ops-build` channel → Developer Mode → right-click → Copy Channel ID
6. Create state dir and files (see above)
7. Create batch file (see above)
8. Double-click batch file → wait for "Listening for channel messages from: plugin:discord@claude-plugins-official"
9. Bot goes green → send test message → verify response

## Critical warnings (from guide)

- **Message Content Intent MUST be ON** — without it bot receives messages with empty content; appears to work but never responds correctly
- **MUST use `plugin:` prefix** — `server:discord` gives MCP tools only, not inbound push; bot will show typing but never receive messages
- **DISCORD_BOT_TOKEN must NOT be set as a Windows environment variable** — it will override the batch file. Remove from System Properties → Environment Variables if present
- **Marketplace sync failure** — if bot shows typing but never responds after a Claude Code update: close ALL sessions, restart one session (lets sync complete cleanly), then restart the rest

## After bot is live

- [x] Update this page status: planned → current (2026-04-24)
- [x] Update CLAUDE.md section 4: remove "reference only" note, add confirmed channel IDs (2026-04-24)
- [x] Commit on feat/phase-2-discord branch (2026-04-24)

## Event types (Phase 2 extensions/notifications/)

JOB_FOUND, CV_READY, REPLY_RECEIVED, INTERVIEW_INVITE, REJECTION, OFFER, GHOST
