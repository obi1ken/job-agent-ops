from __future__ import annotations

import os

import requests

from extensions.quota_manager import QuotaManager
from extensions.quota_manager.models import ClaudeOperation, OperationType, QuotaDecision, WindowSnapshot, Zone


_ZONE_ORDER = [Zone.FREE, Zone.CAUTION, Zone.RESTRICTED, Zone.EMERGENCY]
_API = "https://discord.com/api/v10"


def gate(
    quota: QuotaManager,
    op_type: OperationType,
    tokens: int,
    label: str,
    payload: dict | None = None,
) -> tuple[bool, QuotaDecision]:
    """Check quota. If denied, defer to QuotaManager's PendingQueue.

    Returns (allowed, decision). Caller skips dispatch if not allowed.
    """
    decision = quota.request(op_type, tokens, label)
    if not decision.allowed:
        op = ClaudeOperation(
            operation_type=op_type,
            estimated_tokens=tokens,
            enqueued_at=_now_iso(),
            label=label,
            payload=payload or {},
        )
        quota.defer(op)
    return decision.allowed, decision


def emit_zone_alert_if_changed(
    prev_snap: WindowSnapshot | None,
    curr_snap: WindowSnapshot,
) -> None:
    """Post a plain Discord message if quota zone worsened since last tick."""
    if prev_snap is None:
        return
    if prev_snap.zone == curr_snap.zone:
        return
    prev_level = _ZONE_ORDER.index(prev_snap.zone) if prev_snap.zone in _ZONE_ORDER else 0
    curr_level = _ZONE_ORDER.index(curr_snap.zone) if curr_snap.zone in _ZONE_ORDER else 0
    if curr_level <= prev_level:
        return  # zone improved — no alert needed

    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    channel_id = os.environ.get("DISCORD_CHANNEL_ID", "")
    if not token or not channel_id:
        return

    pct = round(curr_snap.used_pct * 100, 1)
    text = (
        f"⚠️ Quota zone: **{prev_snap.zone.upper()} → {curr_snap.zone.upper()}** "
        f"({pct}% of {curr_snap.window_limit:,} tokens used in window)"
    )
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
    try:
        requests.post(
            f"{_API}/channels/{channel_id}/messages",
            headers=headers,
            json={"content": text},
            timeout=5,
        )
    except Exception:
        pass  # quota alert failure must never break the tick


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
