import os
import re
import shutil
from pathlib import Path
from typing import Optional

_PROVIDER_DOMAINS = {
    "gmail", "googlemail", "yahoo", "hotmail", "outlook", "live",
    "icloud", "me", "mac", "aol", "protonmail", "zoho",
    "reed", "hays", "michaelpage", "robertwalters", "adecco",
    "manpower", "randstad", "totaljobs", "cwjobs", "indeed",
}

COLUMNS = ["date", "company", "role", "track", "score", "portal", "status", "cv_version", "notes"]


class TrackerUpdateError(Exception):
    pass


class TrackerUpdater:
    def __init__(self, applications_md_path: str):
        self._path = Path(applications_md_path)

    def find_and_update(
        self,
        sender_email: str,
        sender_name: str,
        new_status: str,
        notes_suffix: Optional[str] = None,
    ) -> Optional[str]:
        try:
            header_lines, data_rows, col_index = self._read_table()
        except TrackerUpdateError:
            raise

        company_slug = self._extract_company_from_domain(sender_email)
        best_row_idx = self._find_best_row(data_rows, col_index, company_slug, sender_name)

        if best_row_idx is None:
            return None

        matched_company = self._get_cell(data_rows[best_row_idx], col_index, "company")
        data_rows[best_row_idx] = self._update_row(
            data_rows[best_row_idx], col_index, new_status, notes_suffix
        )
        self._write_table(header_lines, data_rows)
        return matched_company

    def _read_table(self) -> tuple[list[str], list[str], dict[str, int]]:
        if not self._path.exists():
            raise TrackerUpdateError(f"applications.md not found: {self._path}")
        lines = self._path.read_text(encoding="utf-8").splitlines()

        header_lines = []
        data_rows = []
        col_index: dict[str, int] = {}
        separator_seen = False

        for line in lines:
            if line.startswith("|") and not separator_seen:
                if re.match(r"^\|[-| ]+\|$", line):
                    separator_seen = True
                    header_lines.append(line)
                    # Parse column names from the previous header line
                    prev = header_lines[-2] if len(header_lines) >= 2 else ""
                    cols = [c.strip().lower().replace(" ", "_") for c in prev.strip("|").split("|")]
                    col_index = {name: i for i, name in enumerate(cols)}
                else:
                    header_lines.append(line)
            elif separator_seen and line.startswith("|"):
                data_rows.append(line)
            else:
                if separator_seen:
                    data_rows.append(line)
                else:
                    header_lines.append(line)

        if not col_index:
            raise TrackerUpdateError("Could not parse column headers from applications.md")
        if "status" not in col_index:
            raise TrackerUpdateError("'Status' column not found in applications.md")

        return header_lines, data_rows, col_index

    def _find_best_row(
        self,
        data_rows: list[str],
        col_index: dict[str, int],
        company_slug: str,
        sender_name: str,
    ) -> Optional[int]:
        if not company_slug:
            return None
        candidates = []
        for i, row in enumerate(data_rows):
            company = self._get_cell(row, col_index, "company").lower()
            company_norm = re.sub(r"[^a-z0-9]", "", company)
            if company_slug and (company_slug in company_norm or company_norm in company_slug):
                status = self._get_cell(row, col_index, "status").lower()
                # Prefer rows that are still active (not rejected/discarded)
                priority = 0 if status in ("applied", "evaluated", "responded") else 1
                candidates.append((priority, i))
        if not candidates:
            return None
        candidates.sort()
        return candidates[0][1]

    def _get_cell(self, row: str, col_index: dict[str, int], col_name: str) -> str:
        cells = [c.strip() for c in row.strip("|").split("|")]
        idx = col_index.get(col_name)
        if idx is None or idx >= len(cells):
            return ""
        return cells[idx]

    def _update_row(
        self,
        row: str,
        col_index: dict[str, int],
        new_status: str,
        notes_suffix: Optional[str],
    ) -> str:
        cells = [c.strip() for c in row.strip("|").split("|")]
        status_idx = col_index["status"]
        if status_idx < len(cells):
            cells[status_idx] = new_status
        if notes_suffix and "notes" in col_index:
            notes_idx = col_index["notes"]
            if notes_idx < len(cells):
                existing = cells[notes_idx]
                cells[notes_idx] = f"{existing}; {notes_suffix}".lstrip("; ")
        return "| " + " | ".join(cells) + " |"

    def _write_table(self, header_lines: list[str], data_rows: list[str]) -> None:
        bak = self._path.with_suffix(".md.bak")
        shutil.copy2(self._path, bak)
        tmp = self._path.with_suffix(".md.tmp")
        content = "\n".join(header_lines + data_rows) + "\n"
        tmp.write_text(content, encoding="utf-8")
        # Sanity check: re-parse the tmp file
        try:
            TrackerUpdater(str(tmp))._read_table()
        except TrackerUpdateError as e:
            tmp.unlink(missing_ok=True)
            raise TrackerUpdateError(f"Write verification failed: {e}") from e
        os.replace(tmp, self._path)

    def _extract_company_from_domain(self, email_address: str) -> str:
        match = re.search(r"@([\w.-]+)", email_address)
        if not match:
            return ""
        domain = match.group(1).lower()
        # Strip TLD and subdomains to get the registrable name
        parts = domain.rstrip(".").split(".")
        # e.g. mail.acme.co.uk → acme; acme.com → acme
        for i in range(len(parts) - 1, -1, -1):
            candidate = re.sub(r"[^a-z0-9]", "", parts[i])
            if candidate and candidate not in _PROVIDER_DOMAINS and len(candidate) > 2:
                return candidate
        return ""
