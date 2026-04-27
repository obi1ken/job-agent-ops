import dataclasses
import json
from pathlib import Path

from .models import DiffEntry, SectionDiff


class DiffLogWriter:
    def __init__(self, log_path: str):
        self._path = Path(log_path)

    def append(self, entry: DiffEntry) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(_entry_to_dict(entry), ensure_ascii=False)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def _entry_to_dict(entry: DiffEntry) -> dict:
    d = dataclasses.asdict(entry)
    # SectionDiff is already handled by asdict recursion
    return d
