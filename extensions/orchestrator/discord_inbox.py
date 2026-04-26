"""Exactly-once Discord inbox.

Two-layer protection against duplicate processing:
  Layer 1 (offset): state tracks byte position in JSONL — restart reads from offset only.
  Layer 2 (message_id): processed_ids set catches replays even when offset is stale.

Write-side dedup: append() checks written_ids before touching the file — same Discord
message arriving twice never produces a duplicate line.

State is saved atomically (.tmp → os.replace) so partial writes never corrupt it.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_INBOX_FILE = "discord_inbox.jsonl"
_STATE_FILE = "discord_inbox_state.json"
_VERSION = 1


class DiscordInbox:
    def __init__(self, state_dir: Path):
        self._inbox = state_dir / _INBOX_FILE
        self._state_path = state_dir / _STATE_FILE
        state_dir.mkdir(parents=True, exist_ok=True)
        self._state = self._load_state()

    # ── Write side ──────────────────────────────────────────────────────────

    def append(
        self,
        message_id: str,
        reply_to_message_id: Optional[str],
        user: str,
        user_id: str,
        text: str,
    ) -> bool:
        """Write message to inbox. Returns False (skips write) if already written."""
        if message_id in self._state["written_ids"]:
            return False

        entry = {
            "received_utc": datetime.now(timezone.utc).isoformat(),
            "message_id": message_id,
            "reply_to_message_id": reply_to_message_id,
            "user": user,
            "user_id": user_id,
            "text": text,
        }
        with self._inbox.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        self._state["written_ids"].add(message_id)
        self._save_state()
        return True

    # ── Read side ────────────────────────────────────────────────────────────

    def read_new(self) -> list[dict]:
        """Read lines since last_offset. Filters out already-processed message_ids."""
        if not self._inbox.exists():
            return []

        messages: list[dict] = []
        with self._inbox.open("rb") as f:
            f.seek(self._state["last_offset"])
            for raw in f:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                mid = entry.get("message_id", "")
                if mid and mid not in self._state["processed_ids"]:
                    messages.append(entry)
        return messages

    def mark_processed(self, message_ids: list[str]) -> None:
        """Record message_ids as processed and advance offset to current EOF.
        Atomic: both offset and processed_ids are saved together."""
        if not message_ids:
            return
        new_offset = self._inbox.stat().st_size if self._inbox.exists() else 0
        self._state["processed_ids"].update(message_ids)
        self._state["last_offset"] = new_offset
        self._save_state()

    # ── State I/O ────────────────────────────────────────────────────────────

    def _load_state(self) -> dict:
        if self._state_path.exists():
            try:
                raw = json.loads(self._state_path.read_text(encoding="utf-8"))
                if raw.get("version") == _VERSION:
                    return {
                        "last_offset": int(raw.get("last_offset", 0)),
                        "processed_ids": set(raw.get("processed_ids", [])),
                        "written_ids": set(raw.get("written_ids", [])),
                    }
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        return {"last_offset": 0, "processed_ids": set(), "written_ids": set()}

    def _save_state(self) -> None:
        tmp = self._state_path.with_suffix(".json.tmp")
        payload = {
            "version": _VERSION,
            "last_offset": self._state["last_offset"],
            "processed_ids": sorted(self._state["processed_ids"]),
            "written_ids": sorted(self._state["written_ids"]),
        }
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self._state_path)
