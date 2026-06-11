from __future__ import annotations

import os
import re
from datetime import timedelta
from typing import Literal

import requests

from .approval_store import PendingApproval

_API = "https://discord.com/api/v10"

_APPROVE_PATTERNS = re.compile(r"\b(approve|approved|yes|go|✅|submit)\b", re.I)
_REJECT_PATTERNS = re.compile(r"\b(reject|rejected|no|skip|pass|❌)\b", re.I)
_DEFER_PATTERNS = re.compile(r"\b(defer|snooze|later|hold)\b", re.I)
_DEFER_WINDOW_RE = re.compile(r"(\d+)\s*(d(?:ay)?s?|h(?:our)?s?)", re.I)

_TRACK_COLORS: dict[str, int] = {
    "A": 0x3498DB, "B": 0x2ECC71, "C": 0xE67E22, "D": 0x9B59B6,
}


def post_approval_request(pending: PendingApproval) -> str | None:
    """Post CV-ready approval embed to Discord.

    Returns Discord message_id of the action prompt, or None on failure.
    """
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    channel_id = os.environ.get("DISCORD_CHANNEL_ID", "")
    charles_id = os.environ.get("DISCORD_USER_ID", "1379195691624038440")
    if not token or not channel_id:
        return None

    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
    color = _TRACK_COLORS.get(pending.track.upper(), 0x3498DB)
    urgent = pending.score >= float(os.environ.get("URGENT_SCORE_FLAG", "4.5"))

    score_label = "⚡ URGENT" if pending.score >= 4.5 else ("★ PRIORITY" if pending.score >= 4.0 else "")
    interest_stage = getattr(pending, "stage", "DOCS") == "INTEREST"
    title = f"Job Match — {pending.company}" if interest_stage else f"CV Ready — {pending.company}"
    if score_label:
        title = f"{score_label} | {title}"

    fields = [
        {"name": "Role", "value": pending.role, "inline": True},
        {"name": "Track", "value": pending.track, "inline": True},
        {"name": "Score", "value": f"{pending.score}/5", "inline": True},
        {"name": "Portal", "value": pending.portal, "inline": True},
        {"name": "Location", "value": getattr(pending, "location", "") or "—", "inline": True},
    ]
    if not interest_stage:
        injected = ", ".join(pending.tailoring_summary.get("keywords_injected", [])[:5]) or "—"
        removed = ", ".join(pending.tailoring_summary.get("keywords_removed", [])[:3]) or "—"
        fields += [
            {"name": "Keywords In", "value": injected, "inline": False},
            {"name": "Keywords Dropped", "value": removed, "inline": False},
            {"name": "CV", "value": pending.cv_path, "inline": False},
            {"name": "Cover Letter", "value": pending.cover_letter_path, "inline": False},
        ]

    embed = {
        "title": title,
        "color": color,
        "fields": fields,
        "footer": {"text": f"approval_id:{pending.approval_id}"},
        "timestamp": pending.created_utc,
    }

    content = f"<@{charles_id}>" if urgent else None
    first_payload: dict = {"embeds": [embed]}
    if content:
        first_payload["content"] = content

    resp = requests.post(
        f"{_API}/channels/{channel_id}/messages",
        headers=headers, json=first_payload, timeout=10,
    )
    resp.raise_for_status()

    # Second message: action prompt
    if interest_stage:
        action_text = (
            f"Interested? Reply **approve** to generate the CV + cover letter, "
            f"or **reject** / **defer N days** for `{pending.approval_id[:8]}`\n"
            f"Job URL: {pending.job_url or '—'}"
        )
    else:
        action_text = (
            f"Reply **approve** / **reject** / **defer N days** for `{pending.approval_id[:8]}`\n"
            f"Job URL: {pending.job_url or '—'}"
        )
    action_payload = {"content": action_text}
    resp2 = requests.post(
        f"{_API}/channels/{channel_id}/messages",
        headers=headers, json=action_payload, timeout=10,
    )
    resp2.raise_for_status()
    return resp2.json().get("id")


def classify_reply(text: str) -> Literal["approve", "reject", "defer", "unknown"]:
    t = text.strip()
    if _APPROVE_PATTERNS.search(t):
        return "approve"
    if _REJECT_PATTERNS.search(t):
        return "reject"
    if _DEFER_PATTERNS.search(t):
        return "defer"
    return "unknown"


def parse_defer_window(text: str) -> timedelta:
    """Parse 'defer 2 days' / 'snooze 3h' / 'later' → timedelta. Default 24h."""
    match = _DEFER_WINDOW_RE.search(text)
    if not match:
        return timedelta(hours=24)
    n = int(match.group(1))
    unit = match.group(2).lower()
    if unit.startswith("h"):
        return timedelta(hours=n)
    return timedelta(days=n)
