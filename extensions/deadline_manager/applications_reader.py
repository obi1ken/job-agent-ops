import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from .models import ApplicationKey, ApplicationRow

_DATE_FMTS = ["%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"]

# Conservative: only accept ISO-ish datetime forms from notes
_DATETIME_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})(?::\d{2})?"
)


class DeadlineManagerError(Exception):
    pass


def _normalize_status(raw: str) -> str:
    return raw.strip().lower()


def _parse_date(value: str) -> Optional[date]:
    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def extract_interview_datetime(notes: str) -> Optional[datetime]:
    match = _DATETIME_RE.search(notes)
    if not match:
        return None
    try:
        dt = datetime.strptime(f"{match.group(1)} {match.group(2)}", "%Y-%m-%d %H:%M")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


class ApplicationsReader:
    def __init__(self, path: str):
        self._path = Path(path)

    def read_all(self) -> list[ApplicationRow]:
        if not self._path.exists():
            raise DeadlineManagerError(f"applications.md not found: {self._path}")

        lines = self._path.read_text(encoding="utf-8").splitlines()
        col_index: dict[str, int] = {}
        separator_seen = False
        header_line = ""
        rows: list[ApplicationRow] = []

        for line in lines:
            if not line.startswith("|"):
                continue
            if re.match(r"^\|[-| ]+\|$", line):
                separator_seen = True
                cols = [c.strip().lower().replace(" ", "_") for c in header_line.strip("|").split("|")]
                col_index = {name: i for i, name in enumerate(cols)}
                self._validate_columns(col_index)
                continue
            if not separator_seen:
                header_line = line
                continue
            row = self._parse_row(line, col_index)
            if row is not None:
                rows.append(row)

        return rows

    def _validate_columns(self, col_index: dict[str, int]) -> None:
        for required in ("date", "company", "role", "status"):
            if required not in col_index:
                raise DeadlineManagerError(f"malformed table: missing column '{required}'")

    def _parse_row(self, line: str, col_index: dict[str, int]) -> Optional[ApplicationRow]:
        cells = [c.strip() for c in line.strip("|").split("|")]

        def cell(name: str) -> str:
            idx = col_index.get(name)
            if idx is None or idx >= len(cells):
                return ""
            return cells[idx].strip()

        company = cell("company")
        role = cell("role")
        date_str = cell("date")

        if not company or not role or not date_str:
            return None

        parsed_date = _parse_date(date_str)
        if parsed_date is None:
            return None

        status_raw = cell("status")
        key = ApplicationKey.from_parts(company, role, parsed_date.isoformat())

        return ApplicationRow(
            key=key,
            company_display=company,
            role_display=role,
            track=cell("track"),
            score=cell("score"),
            portal=cell("portal"),
            status_raw=status_raw,
            status_norm=_normalize_status(status_raw),
            date_applied=parsed_date,
            cv_version=cell("cv_version"),
            notes=cell("notes"),
        )
