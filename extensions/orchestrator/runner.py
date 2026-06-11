"""Orchestrator tick — ties all 6 extensions together.

Each phase is independently try/except'd. A failing phase never blocks others.
Tick is designed to run once and exit (cron-friendly). No daemon loop here.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from extensions.deadline_manager import run_tick as deadline_tick
from extensions.job_discovery import JobDiscovery, JobListing
from extensions.notifications import DiscordNotifier
from extensions.quota_manager import QuotaManager, get_manager

from . import result_handlers
from .ai_prompts import build_interview_prep_prompt, build_score_prompt
from .ai_task_queue import AITaskKind, AITaskQueue
from .approval_dispatcher import classify_reply, parse_defer_window, post_approval_request
from .approval_store import ApprovalState, ApprovalStore
from .config import ProfileConfig, load_profile
from .discord_inbox import DiscordInbox
from .quota_gate import emit_zone_alert_if_changed, gate
from .review_queue import APPROVED as RQ_APPROVED
from .review_queue import EXPIRED as RQ_EXPIRED
from .review_queue import REJECTED as RQ_REJECTED
from .review_queue import ReviewQueue
from .submission import submit_approved

log = logging.getLogger(__name__)


@dataclass
class TickReport:
    started_utc: str = ""
    finished_utc: str = ""
    email_results: list[dict] = field(default_factory=list)
    deadline_follow_ups: int = 0
    deadline_ghosts: int = 0
    new_jobs: int = 0
    ai_tasks_dispatched: int = 0
    ai_tasks_consumed: int = 0
    approvals_processed: int = 0
    submissions: int = 0
    expired_approvals: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class TickContext:
    """Shared references threaded through phases — avoids global state."""
    config: ProfileConfig
    quota: QuotaManager
    notifier: DiscordNotifier
    ai_queue: AITaskQueue
    approval_store: ApprovalStore
    discord_inbox: DiscordInbox
    review_queue: "ReviewQueue"
    now_utc: datetime
    report: TickReport


class Orchestrator:
    def __init__(
        self,
        project_root: Optional[str] = None,
        config: Optional[ProfileConfig] = None,
    ):
        self._config = config or load_profile(project_root)
        self._config.orchestrator_dir.mkdir(parents=True, exist_ok=True)
        self._config.output_dir.mkdir(parents=True, exist_ok=True)
        self._config.jds_dir.mkdir(parents=True, exist_ok=True)

    def tick(self) -> TickReport:
        now_utc = datetime.now(timezone.utc)
        report = TickReport(started_utc=now_utc.isoformat())
        cfg = self._config

        quota = get_manager()
        prev_snap = quota.snapshot()

        ctx = TickContext(
            config=cfg,
            quota=quota,
            notifier=DiscordNotifier(),
            ai_queue=AITaskQueue(cfg.ai_outbox_dir, cfg.ai_inbox_dir, cfg.orchestrator_dir),
            approval_store=ApprovalStore(cfg.orchestrator_dir),
            discord_inbox=DiscordInbox(cfg.orchestrator_dir),
            review_queue=ReviewQueue(cfg.orchestrator_dir),
            now_utc=now_utc,
            report=report,
        )

        phases = [
            ("email_poll", self._phase_email_poll),
            ("deadline_tick", self._phase_deadline_tick),
            ("consume_ai_results", self._phase_consume_ai_results),
            ("process_approvals", self._phase_process_approvals),
            ("present_next", self._phase_present_next),
            ("job_discovery", self._phase_job_discovery),
            ("dispatch_ai_tasks", self._phase_dispatch_ai_tasks),
            ("flush_quota_queue", self._phase_flush_quota_queue),
        ]

        for name, fn in phases:
            try:
                fn(ctx)
            except Exception as exc:
                msg = f"phase {name}: {exc}"
                log.error(msg, exc_info=True)
                report.errors.append(msg)

        curr_snap = quota.snapshot()
        emit_zone_alert_if_changed(prev_snap, curr_snap)

        self._persist_report(report, cfg)
        report.finished_utc = datetime.now(timezone.utc).isoformat()
        return report

    # ── Phases ───────────────────────────────────────────────────────────────

    def _phase_email_poll(self, ctx: TickContext) -> None:
        try:
            from extensions.email_monitor import EmailMonitor
        except ImportError:
            return

        credentials = os.environ.get("GMAIL_CREDENTIALS_PATH", "")
        token = os.environ.get("GMAIL_TOKEN_PATH", "")
        if not credentials or not token:
            log.debug("Gmail credentials not configured — skipping email poll")
            return

        monitor = EmailMonitor(
            credentials_path=credentials,
            token_path=token,
            data_dir=str(ctx.config.project_root),
            state_dir=os.path.dirname(token),
        )
        monitor.authenticate()
        results = monitor.poll()
        ctx.report.email_results = results

        # Queue interview prep for any INTERVIEW_INVITE
        for r in results:
            if r.get("email_class") == "INTERVIEW_INVITE":
                self._queue_interview_prep(
                    company=r.get("company_matched") or "Unknown",
                    role=r.get("subject", "")[:60],
                    track="A",  # orchestrator doesn't know track from email alone — default A
                    jd_text="",
                    ctx=ctx,
                )

    def _phase_deadline_tick(self, ctx: TickContext) -> None:
        result = deadline_tick()
        ctx.report.deadline_follow_ups = len(result.follow_ups_sent)
        ctx.report.deadline_ghosts = len(result.ghosts_emitted)
        if result.errors:
            ctx.report.errors.extend([f"deadline: {e}" for e in result.errors])

    def _phase_consume_ai_results(self, ctx: TickContext) -> None:
        consumed = ctx.ai_queue.consume_completed()
        ctx.report.ai_tasks_consumed = len(consumed)
        for task, raw in consumed:
            try:
                result_handlers.dispatch(task, raw, ctx)
            except Exception as exc:
                log.error("result_handler failed for task %s: %s", task.task_id[:8], exc)
                ctx.report.errors.append(f"result_handler:{task.kind}:{exc}")

        stale = ctx.ai_queue.drain_stale()
        for t in stale:
            log.warning("AI task stale — no output after 2h: %s (%s)", t.task_id[:8], t.kind)

    def _phase_process_approvals(self, ctx: TickContext) -> None:
        # Expire stale AWAITING approvals
        expired = ctx.approval_store.expire_stale(ctx.now_utc)
        ctx.report.expired_approvals = len(expired)
        for aid in expired:
            ctx.review_queue.mark_by_approval(aid, RQ_EXPIRED)

        # Re-present DEFERRED approvals that are now due
        for pending in ctx.approval_store.list_due_for_retry(ctx.now_utc):
            try:
                msg_id = post_approval_request(pending)
                if msg_id:
                    ctx.approval_store.transition(
                        pending.approval_id, ApprovalState.AWAITING,
                        discord_message_id=msg_id,
                    )
            except Exception as exc:
                log.error("Re-present deferred approval failed: %s", exc)

        # Process new Discord replies
        new_messages = ctx.discord_inbox.read_new()
        processed_ids = []
        for msg in new_messages:
            mid = msg.get("message_id", "")
            reply_to = msg.get("reply_to_message_id")
            text = msg.get("text", "")

            pending = None
            if reply_to:
                pending = ctx.approval_store.find_by_message_id(reply_to)
            if pending is None:
                # Try matching by approval_id in text (Charles may reference it)
                for a in ctx.approval_store.list_awaiting():
                    if a.approval_id[:8] in text:
                        pending = a
                        break

            if pending is None:
                log.debug("No pending approval matched for message %s", mid[:8])
                processed_ids.append(mid)
                continue

            action = classify_reply(text)
            try:
                self._handle_approval_action(pending, action, text, ctx)
                ctx.report.approvals_processed += 1
            except Exception as exc:
                log.error("Approval action failed for %s: %s", pending.approval_id[:8], exc)
                ctx.report.errors.append(f"approval:{pending.approval_id[:8]}:{exc}")
            processed_ids.append(mid)

        if processed_ids:
            ctx.discord_inbox.mark_processed(processed_ids)

    def _handle_approval_action(
        self, pending, action: str, text: str, ctx: TickContext
    ) -> None:
        if action == "approve":
            if getattr(pending, "stage", "DOCS") == "INTEREST":
                # Stage 1 approved: Charles is interested — generate documents now.
                ctx.approval_store.transition(pending.approval_id, ApprovalState.APPROVED)
                result_handlers.dispatch_tailoring(pending, ctx)
                log.info("INTERESTED: %s — %s (Track %s) — generating documents",
                         pending.company, pending.role, pending.track)
                return
            ctx.approval_store.transition(pending.approval_id, ApprovalState.APPROVED)
            submit_approved(pending, ctx.config)
            ctx.approval_store.transition(pending.approval_id, ApprovalState.SUBMITTED)
            ctx.review_queue.mark_by_approval(pending.approval_id, RQ_APPROVED)
            ctx.report.submissions += 1
            log.info("SUBMITTED: %s — %s (Track %s)", pending.company, pending.role, pending.track)

        elif action == "reject":
            ctx.approval_store.transition(pending.approval_id, ApprovalState.REJECTED, notes=text)
            ctx.review_queue.mark_by_approval(pending.approval_id, RQ_REJECTED)
            log.info("REJECTED: %s — %s", pending.company, pending.role)

        elif action == "defer":
            window = parse_defer_window(text)
            defer_until = (ctx.now_utc + window).isoformat()
            ctx.approval_store.transition(
                pending.approval_id, ApprovalState.DEFERRED,
                notes=text, defer_until_utc=defer_until,
            )
            log.info("DEFERRED: %s until %s", pending.company, defer_until[:10])

        else:
            log.debug("Unknown approval action '%s' for %s", action, pending.approval_id[:8])

    def _phase_present_next(self, ctx: TickContext) -> None:
        result_handlers.present_next_job(ctx)

    def _phase_job_discovery(self, ctx: TickContext) -> None:
        portals_yml = ctx.config.portals_yml_path
        if not portals_yml.exists():
            log.debug("portals.yml not found — skipping job discovery")
            return

        discovery = JobDiscovery(portals_yml_path=str(portals_yml))
        listings = discovery.run()
        ctx.report.new_jobs = len(listings)

        for listing in listings:
            self._queue_score_job(listing, ctx)

    def _phase_dispatch_ai_tasks(self, ctx: TickContext) -> None:
        # Tasks are already dispatched (written to outbox) during enqueue.
        # This phase just reports the count for the tick summary.
        ctx.report.ai_tasks_dispatched = len(ctx.ai_queue.list_awaiting())

    def _phase_flush_quota_queue(self, ctx: TickContext) -> None:
        eligible = ctx.quota.flush_queue()
        for op in eligible:
            decision = ctx.quota.request(op.operation_type, op.estimated_tokens, op.label)
            if not decision.allowed:
                continue
            ctx.quota.confirm_dequeued(op)
            listing_data = op.payload.get("listing")
            if listing_data and op.operation_type.name.startswith("JD_SCORING"):
                # Rebuild the score task that was deferred — without this the
                # listing is marked seen but never scored (silently lost).
                try:
                    self._queue_score_job(JobListing(**listing_data), ctx)
                    log.info("Quota queue: re-dispatched deferred score %s", op.label)
                except (TypeError, KeyError) as exc:
                    log.error("Quota queue: failed to rebuild %s: %s", op.label, exc)
            else:
                log.info("Quota queue: released deferred op %s (no rebuild payload)", op.label)
        ctx.quota.drain_stale_queue()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _queue_score_job(self, listing: JobListing, ctx: TickContext) -> None:
        from extensions.quota_manager.models import OperationType
        urgent = getattr(listing, "seniority_boost", False)
        op = OperationType.JD_SCORING_URGENT if urgent else OperationType.JD_SCORING_STANDARD
        prompt, tokens = build_score_prompt(
            listing.description or listing.title,
            listing.company,
            listing.title,
            ctx.config,
        )
        allowed, _ = gate(
            ctx.quota, op, tokens, f"score:{listing.company[:20]}",
            {
                "listing_id": listing.external_id,
                # Full listing snapshot so a quota-deferred score can be
                # rebuilt by the flush phase (raw omitted to keep state small)
                "listing": {
                    "source": listing.source,
                    "external_id": listing.external_id,
                    "title": listing.title,
                    "company": listing.company,
                    "location": listing.location,
                    "description": listing.description,
                    "url": listing.url,
                    "salary_min": listing.salary_min,
                    "salary_max": listing.salary_max,
                    "posted_date": listing.posted_date,
                    "seniority_boost": listing.seniority_boost,
                },
            },
        )
        if not allowed:
            return

        jd_path = self._save_jd(listing, ctx.config)
        ctx.ai_queue.enqueue(
            kind=AITaskKind.SCORE_JD,
            operation_type_name=op.name,
            estimated_tokens=tokens,
            payload={
                "company": listing.company, "role": listing.title,
                "jd_text": listing.description or listing.title,
                "jd_path": jd_path, "portal": listing.source,
                "job_url": listing.url,
                "location": getattr(listing, "location", ""),
                "external_id": listing.external_id,
            },
            prompt_text=prompt,
        )
        ctx.quota.record_usage(tokens, op)

    def _queue_interview_prep(
        self, company: str, role: str, track: str, jd_text: str, ctx: TickContext
    ) -> None:
        from extensions.quota_manager.models import OperationType
        op = OperationType.INTERVIEW_INVITE_RESPONSE
        prompt, tokens = build_interview_prep_prompt(jd_text, company, role, track)
        allowed, _ = gate(ctx.quota, op, tokens, f"prep:{company[:20]}", {})
        if not allowed:
            log.warning("Interview prep deferred for %s — quota", company)
            return
        ctx.ai_queue.enqueue(
            kind=AITaskKind.INTERVIEW_PREP,
            operation_type_name=op.name,
            estimated_tokens=tokens,
            payload={"company": company, "role": role, "track": track, "jd_text": jd_text},
            prompt_text=prompt,
        )
        ctx.quota.record_usage(tokens, op)

    def _save_jd(self, listing: JobListing, config: ProfileConfig) -> str:
        import re as _re
        safe = _re.sub(r"[^\w]", "_", listing.company)[:20]
        safe_id = _re.sub(r"[^\w\-]", "_", listing.external_id)[:12]
        filename = f"{safe_id}_{safe}.txt"
        path = config.jds_dir / filename
        config.jds_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"{listing.title}\n{listing.company}\n{listing.url}\n\n{listing.description or ''}",
            encoding="utf-8",
        )
        return str(path)

    def _persist_report(self, report: TickReport, config: ProfileConfig) -> None:
        log_path = config.output_dir / "orchestrator_tick.jsonl"
        config.output_dir.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(report)) + "\n")
