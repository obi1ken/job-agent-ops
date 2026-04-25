import os

import requests

from .models import PrepResult, PrepSection

_API = "https://discord.com/api/v10"
_EMBED_MAX = 4000

_TRACK_COLORS: dict[str, int] = {
    "A": 0x3498DB,  # blue
    "B": 0x2ECC71,  # green
    "C": 0xE67E22,  # orange
    "D": 0x9B59B6,  # purple
}
_TRACK_LABELS: dict[str, str] = {
    "A": "Engineering",
    "B": "Product & Leadership",
    "C": "Rail/Civils Digital",
    "D": "Document Control",
}


def deliver(result: PrepResult) -> None:
    token = os.environ["DISCORD_BOT_TOKEN"]
    channel_id = os.environ["DISCORD_CHANNEL_ID"]
    charles_id = os.environ.get("DISCORD_USER_ID", "1379195691624038440")
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
    }

    color = _TRACK_COLORS.get(result.track.upper(), 0x3498DB)
    sec = {s.name: s for s in result.sections}

    embeds = [
        _embed_overview(result, sec.get("Company Research"), color),
        _embed_fit(result, sec.get("Role Fit"), sec.get("Proof Points"), color),
        _embed_questions(result, sec.get("Likely Questions"), color),
        _embed_flags(result, sec.get("Red Flags"), color),
    ]

    first = {
        "content": f"<@{charles_id}> Interview prep ready: **{result.company}** — {result.role}",
        "embeds": [embeds[0]],
    }
    _post(f"{_API}/channels/{channel_id}/messages", headers, first)

    for embed in embeds[1:]:
        _post(f"{_API}/channels/{channel_id}/messages", headers, {"embeds": [embed]})


def _post(url: str, headers: dict, payload: dict) -> None:
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp.raise_for_status()


def _embed_overview(result: PrepResult, section: PrepSection | None, color: int) -> dict:
    research = _trunc(section.content if section else "[No content]")
    track_label = _TRACK_LABELS.get(result.track.upper(), result.track)
    description = f"**Role:** {result.role}  |  **Track:** {result.track} — {track_label}\n\n**Company Research**\n\n{research}"
    return {
        "title": f"Interview Prep — {result.company}",
        "description": _trunc(description),
        "color": color,
        "timestamp": result.timestamp_utc,
        "footer": {"text": "job-agent-ops | interview prep"},
    }


def _embed_fit(result: PrepResult, fit: PrepSection | None, proof: PrepSection | None, color: int) -> dict:
    fit_text = _trunc(fit.content if fit else "[No content]", 1800)
    proof_text = _trunc(proof.content if proof else "[No content]", 1800)
    description = f"**Role Fit**\n\n{fit_text}\n\n**Proof Points**\n\n{proof_text}"
    return {
        "title": "Fit & Proof Points",
        "description": _trunc(description),
        "color": color,
    }


def _embed_questions(result: PrepResult, section: PrepSection | None, color: int) -> dict:
    return {
        "title": "Likely Questions",
        "description": _trunc(section.content if section else "[No content]"),
        "color": color,
    }


def _embed_flags(result: PrepResult, section: PrepSection | None, color: int) -> dict:
    flags = _trunc(section.content if section else "[No content]", 1800)
    description = (
        f"**Red Flags**\n\n{flags}\n\n"
        f"─────\nTrack {result.track} | {result.timestamp_utc[:10]}"
    )
    return {
        "title": "Red Flags & Metadata",
        "description": _trunc(description),
        "color": color,
    }


def _trunc(text: str, max_chars: int = _EMBED_MAX) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."
