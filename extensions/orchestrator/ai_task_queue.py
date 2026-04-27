from __future__ import annotations

import json
import os
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

_STATE_FILE = "ai_tasks.json"
_VERSION = 1
_STALE_HOURS = 2


class AITaskKind(str, Enum):
    SCORE_JD = "SCORE_JD"
    TAILOR_CV = "TAILOR_CV"
    COVER_LETTER = "COVER_LETTER"
    INTERVIEW_PREP = "INTERVIEW_PREP"


class AITaskStatus(str, Enum):
    PENDING_DISPATCH = "PENDING_DISPATCH"
    AWAITING_OUTPUT = "AWAITING_OUTPUT"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


@dataclass
class AITask:
    task_id: str
    kind: str                       # AITaskKind value
    operation_type_name: str        # OperationType name for QuotaManager
    estimated_tokens: int
    payload: dict
    prompt_path: str
    output_path: str
    related_approval_id: Optional[str]
    created_utc: str
    status: str                     # AITaskStatus value
    error: str = ""


class AITaskQueue:
    def __init__(self, outbox_dir: Path, inbox_dir: Path, state_dir: Path):
        self._outbox = outbox_dir
        self._inbox = inbox_dir
        self._archive = inbox_dir / "_archive"
        self._state_path = state_dir / _STATE_FILE
        self._tasks: dict[str, AITask] = {}
        outbox_dir.mkdir(parents=True, exist_ok=True)
        inbox_dir.mkdir(parents=True, exist_ok=True)
        self._archive.mkdir(parents=True, exist_ok=True)
        self._load()

    def enqueue(
        self,
        kind: AITaskKind,
        operation_type_name: str,
        estimated_tokens: int,
        payload: dict,
        prompt_text: str,
        related_approval_id: Optional[str] = None,
    ) -> AITask:
        task_id = str(uuid.uuid4())
        prompt_filename = f"{task_id}.{kind.value}.prompt.md"
        output_filename = f"{task_id}.{kind.value}.output.md"
        prompt_path = str(self._outbox / prompt_filename)
        output_path = str(self._inbox / output_filename)

        # Write prompt file with front-matter so Claude Code knows where to write output
        full_prompt = (
            f"---\n"
            f"task_id: {task_id}\n"
            f"kind: {kind.value}\n"
            f"write_output_to: {output_path}\n"
            f"---\n"
            f"[Claude Code: execute the instructions below and write output to the path above.]\n\n"
            f"{prompt_text}"
        )
        Path(prompt_path).write_text(full_prompt, encoding="utf-8")

        task = AITask(
            task_id=task_id,
            kind=kind.value,
            operation_type_name=operation_type_name,
            estimated_tokens=estimated_tokens,
            payload=payload,
            prompt_path=prompt_path,
            output_path=output_path,
            related_approval_id=related_approval_id,
            created_utc=datetime.now(timezone.utc).isoformat(),
            status=AITaskStatus.AWAITING_OUTPUT.value,
        )
        self._tasks[task_id] = task
        self._save()
        return task

    def consume_completed(self) -> list[tuple[AITask, str]]:
        """Scan inbox for output files matching awaiting tasks. Returns (task, raw_output) pairs."""
        results = []
        awaiting = [t for t in self._tasks.values() if t.status == AITaskStatus.AWAITING_OUTPUT.value]
        for task in awaiting:
            output_path = Path(task.output_path)
            if not output_path.exists():
                continue
            try:
                raw = output_path.read_text(encoding="utf-8")
            except OSError:
                continue
            # Archive output file
            archive_path = self._archive / output_path.name
            shutil.move(str(output_path), str(archive_path))
            task.status = AITaskStatus.COMPLETE.value
            results.append((task, raw))

        if results:
            self._save()
        return results

    def fail(self, task_id: str, reason: str) -> None:
        t = self._tasks.get(task_id)
        if t:
            t.status = AITaskStatus.FAILED.value
            t.error = reason
            self._save()

    def list_awaiting(self) -> list[AITask]:
        return [t for t in self._tasks.values() if t.status == AITaskStatus.AWAITING_OUTPUT.value]

    def drain_stale(self, max_age_hours: int = _STALE_HOURS) -> list[AITask]:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        stale = []
        for t in self._tasks.values():
            if t.status != AITaskStatus.AWAITING_OUTPUT.value:
                continue
            try:
                created = datetime.fromisoformat(t.created_utc)
                if created < cutoff:
                    t.status = AITaskStatus.FAILED.value
                    t.error = f"stale: no output after {max_age_hours}h"
                    stale.append(t)
            except ValueError:
                pass
        if stale:
            self._save()
        return stale

    def _load(self) -> None:
        if not self._state_path.exists():
            return
        try:
            raw = json.loads(self._state_path.read_text(encoding="utf-8"))
            if raw.get("version") != _VERSION:
                return
            for item in raw.get("tasks", []):
                try:
                    t = AITask(**item)
                    self._tasks[t.task_id] = t
                except (TypeError, KeyError):
                    pass
        except (json.JSONDecodeError, KeyError):
            pass

    def _save(self) -> None:
        tmp = self._state_path.with_suffix(".json.tmp")
        payload = {
            "version": _VERSION,
            "tasks": [asdict(t) for t in self._tasks.values()],
        }
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self._state_path)
