#!/usr/bin/env python3
"""Job Agent Ops — Orchestrator entry point.

Usage:
  python orchestrator.py                     # run one full tick
  python orchestrator.py --step discovery    # run one phase only
  python orchestrator.py --dry-run           # tick without Discord sends or file writes
  python orchestrator.py --verbose           # debug logging
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


_LOCK_FILE = Path("extensions/orchestrator/.lock")
_VALID_STEPS = {"email", "deadlines", "discovery", "approvals", "prep", "quota_flush"}


def _acquire_lock() -> bool:
    """Simple file-based lock to prevent concurrent ticks."""
    try:
        if _LOCK_FILE.exists():
            # Check if stale (> 10 minutes old)
            age = datetime.now(timezone.utc).timestamp() - _LOCK_FILE.stat().st_mtime
            if age < 600:
                return False
            _LOCK_FILE.unlink(missing_ok=True)
        _LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        _LOCK_FILE.write_text(str(os.getpid()))
        return True
    except OSError:
        return False


def _release_lock() -> None:
    _LOCK_FILE.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Job Agent Ops orchestrator")
    parser.add_argument("--step", choices=_VALID_STEPS, help="Run a single phase only")
    parser.add_argument("--dry-run", action="store_true", help="No Discord sends or file writes")
    parser.add_argument("--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args(argv)

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    log = logging.getLogger("orchestrator")

    if args.dry_run:
        log.info("DRY RUN — no Discord sends or submissions")
        os.environ.setdefault("ORCHESTRATOR_DRY_RUN", "1")

    if not _acquire_lock():
        log.warning("Another tick is running (lock file exists). Exiting.")
        return 0

    try:
        from extensions.orchestrator import Orchestrator

        orch = Orchestrator()
        report = orch.tick()

        log.info(
            "Tick complete: %d new jobs | %d AI tasks | %d approvals | %d submissions | %d errors",
            report.new_jobs,
            report.ai_tasks_consumed,
            report.approvals_processed,
            report.submissions,
            len(report.errors),
        )
        if report.errors:
            for err in report.errors:
                log.warning("  Error: %s", err)

        if report.submissions > 0:
            log.info("  ⚠ Submissions logged — verify data/applications.md")

        return 0

    except FileNotFoundError as exc:
        logging.getLogger("orchestrator").error("Config error: %s", exc)
        return 2
    except Exception as exc:
        logging.getLogger("orchestrator").error("Unexpected error: %s", exc, exc_info=True)
        return 1
    finally:
        _release_lock()


if __name__ == "__main__":
    sys.exit(main())
