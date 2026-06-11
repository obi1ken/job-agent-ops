"""Parse Claude Code's output for each AI task kind and drive the next stage."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from extensions.cv_diff import CvDiffer
from extensions.interview_prep import PrepBuilder, PrepInput
from extensions.quota_manager.models import OperationType

from .ai_task_queue import AITask, AITaskKind
from .approval_dispatcher import post_approval_request
from .approval_store import PendingApproval, ApprovalState

if TYPE_CHECKING:
    from .runner import TickContext

log = logging.getLogger(__name__)

_RESULT_RE = re.compile(r"<<<RESULT_JSON>>>\s*(\{.*?\})\s*<<<END>>>", re.DOTALL)


def _parse_result_json(raw: str) -> dict[str, Any]:
    match = _RESULT_RE.search(raw)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}


def handle_score_result(task: AITask, raw: str, ctx: "TickContext") -> None:
    result = _parse_result_json(raw)
    if not result:
        log.warning("SCORE_JD task %s: no result JSON found", task.task_id[:8])
        return

    best_track = result.get("best_track", "A")
    score = float(result.get("score", 0.0))
    above = result.get("above_threshold", False)
    edms_platform = result.get("edms_platform")

    company = task.payload.get("company", "")
    role = task.payload.get("role", "")
    jd_path = task.payload.get("jd_path", "")
    portal = task.payload.get("portal", "")
    job_url = task.payload.get("job_url", "")
    location = task.payload.get("location", "")

    threshold = ctx.config.scoring.threshold_for(best_track)
    if score < threshold:
        log.info("SCORE_JD %s: score %.1f < threshold %.1f for Track %s — skipped",
                 task.task_id[:8], score, threshold, best_track)
        return

    # Two-stage approval: present the job match first. CV/cover letter are
    # only generated after Charles approves interest (token control).
    pending = PendingApproval.create(
        company=company, role=role, track=best_track, score=score,
        portal=portal, job_url=job_url,
        cv_path="", cover_letter_path="", jd_path=jd_path,
        tailoring_summary={"edms_platform": edms_platform},
        stage="INTEREST", location=location,
    )
    ctx.approval_store.add(pending)
    log.info("INTEREST approval created for %s (Track %s, %.1f)", company, best_track, score)

    try:
        msg_id = post_approval_request(pending)
        if msg_id:
            ctx.approval_store.transition(
                pending.approval_id, ApprovalState.AWAITING,
                discord_message_id=msg_id,
            )
    except Exception as exc:
        log.error("Failed to post interest approval for %s: %s", company, exc)


def dispatch_tailoring(pending: PendingApproval, ctx: "TickContext") -> None:
    """Charles approved interest — generate the documents. Called from the
    approval-action handler, never directly from scoring."""
    from extensions.quota_manager.models import OperationType
    from .ai_prompts import build_tailor_cv_prompt
    from .quota_gate import gate

    jd_text = _read_jd_text(pending.jd_path)
    edms_platform = pending.tailoring_summary.get("edms_platform")

    op = OperationType.CV_TAILORING_STANDARD
    prompt, tokens = build_tailor_cv_prompt(
        jd_text, pending.track, pending.company, pending.role, ctx.config
    )
    allowed, _ = gate(ctx.quota, op, tokens, f"tailor:{pending.company[:20]}", {})
    if not allowed:
        log.info("TAILOR_CV deferred for %s — quota", pending.company)
        return

    tailor_task = ctx.ai_queue.enqueue(
        kind=AITaskKind.TAILOR_CV,
        operation_type_name=op.name,
        estimated_tokens=tokens,
        payload={
            "company": pending.company, "role": pending.role, "track": pending.track,
            "score": pending.score, "portal": pending.portal, "job_url": pending.job_url,
            "jd_text": jd_text, "jd_path": pending.jd_path,
            "edms_platform": edms_platform,
            "approval_id": pending.approval_id,
        },
        prompt_text=prompt,
        related_approval_id=pending.approval_id,
    )
    ctx.quota.record_usage(tokens, op)
    log.info("TAILOR_CV task %s enqueued for %s (Track %s, %.1f)",
             tailor_task.task_id[:8], pending.company, pending.track, pending.score)


def _read_jd_text(jd_path: str) -> str:
    try:
        return Path(jd_path).read_text(encoding="utf-8")
    except OSError:
        return ""


def handle_tailor_cv_result(task: AITask, raw: str, ctx: "TickContext") -> None:
    result = _parse_result_json(raw)
    payload = task.payload
    company = payload.get("company", "")
    role = payload.get("role", "")
    track = payload.get("track", "A")
    score = float(payload.get("score", 0.0))
    portal = payload.get("portal", "")
    job_url = payload.get("job_url", "")
    jd_text = payload.get("jd_text", "")
    jd_path = payload.get("jd_path", "")
    edms_platform = payload.get("edms_platform")

    # Save tailored CV
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    safe_company = re.sub(r"[^\w]", "_", company)[:20]
    cv_filename = f"cv_{safe_company}_{ts}.md"
    cv_path = ctx.config.output_dir / cv_filename
    ctx.config.output_dir.mkdir(parents=True, exist_ok=True)

    # Extract CV text (everything before <<<RESULT_JSON>>>)
    cv_text = raw.split("<<<RESULT_JSON>>>")[0].strip()
    cv_path.write_text(cv_text, encoding="utf-8")

    # Run cv_diff
    tailoring_summary: dict = {
        "keywords_injected": result.get("keywords_injected", []),
        "keywords_removed": result.get("keywords_removed", []),
        "profile_block_used": result.get("profile_block_used", ""),
    }
    try:
        if ctx.config.cv_master_path.exists():
            differ = CvDiffer(str(ctx.config.cv_master_path))
            diff_entry = differ.compute_diff(
                tailored_md=cv_text,
                track=track,
                jd_keywords=result.get("keywords_injected", []),
                company=company,
                role=role,
            )
            tailoring_summary["keywords_injected"] = diff_entry.keywords_injected
            tailoring_summary["keywords_removed"] = diff_entry.keywords_removed
    except Exception as exc:
        log.warning("cv_diff failed for %s: %s", company, exc)

    # Enqueue COVER_LETTER
    from .ai_prompts import build_cover_letter_prompt
    from .quota_gate import gate

    op = OperationType.COVER_LETTER_STANDARD
    prompt, tokens = build_cover_letter_prompt(
        jd_text, str(cv_path), track, company, role, edms_platform, ctx.config
    )
    allowed, _ = gate(ctx.quota, op, tokens, f"cover:{company[:20]}", {})
    if not allowed:
        log.info("COVER_LETTER deferred for %s — quota", company)
        return

    ctx.ai_queue.enqueue(
        kind=AITaskKind.COVER_LETTER,
        operation_type_name=op.name,
        estimated_tokens=tokens,
        payload={
            "company": company, "role": role, "track": track,
            "score": score, "portal": portal, "job_url": job_url,
            "jd_text": jd_text, "jd_path": jd_path,
            "cv_path": str(cv_path), "tailoring_summary": tailoring_summary,
            "approval_id": payload.get("approval_id", ""),
        },
        prompt_text=prompt,
        related_approval_id=payload.get("approval_id") or None,
    )
    ctx.quota.record_usage(tokens, op)


def handle_cover_letter_result(task: AITask, raw: str, ctx: "TickContext") -> None:
    payload = task.payload
    company = payload.get("company", "")
    role = payload.get("role", "")
    track = payload.get("track", "A")
    score = float(payload.get("score", 0.0))
    cv_path = payload.get("cv_path", "")
    tailoring_summary = payload.get("tailoring_summary", {})

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    safe_company = re.sub(r"[^\w]", "_", company)[:20]
    cl_filename = f"cover_{safe_company}_{ts}.md"
    cl_path = ctx.config.output_dir / cl_filename
    cl_text = raw.split("<<<RESULT_JSON>>>")[0].strip()
    cl_path.write_text(cl_text, encoding="utf-8")

    approval_id = payload.get("approval_id", "")
    pending = None
    if approval_id:
        # Two-stage flow: attach docs to the interest approval Charles already said yes to
        pending = ctx.approval_store.attach_documents(
            approval_id, cv_path, str(cl_path), tailoring_summary
        )

    if pending is None:
        # Legacy path: no prior interest approval — create one at the DOCS stage
        pending = PendingApproval.create(
            company=company, role=role, track=track, score=score,
            portal=payload.get("portal", ""),
            job_url=payload.get("job_url", ""),
            cv_path=cv_path,
            cover_letter_path=str(cl_path),
            jd_path=payload.get("jd_path", ""),
            tailoring_summary=tailoring_summary,
        )
        ctx.approval_store.add(pending)

    try:
        msg_id = post_approval_request(pending)
        if msg_id:
            ctx.approval_store.transition(
                pending.approval_id, ApprovalState.AWAITING,
                discord_message_id=msg_id,
            )
    except Exception as exc:
        log.error("Failed to post approval request for %s: %s", company, exc)


def handle_interview_prep_result(task: AITask, raw: str, ctx: "TickContext") -> None:
    payload = task.payload
    prep_input = PrepInput(
        jd_text=payload.get("jd_text", ""),
        company=payload.get("company", ""),
        role=payload.get("role", ""),
        track=payload.get("track", "A"),
    )
    try:
        PrepBuilder().finalise(prep_input, raw)
    except Exception as exc:
        log.error("interview_prep finalise failed: %s", exc)


_HANDLERS = {
    AITaskKind.SCORE_JD.value: handle_score_result,
    AITaskKind.TAILOR_CV.value: handle_tailor_cv_result,
    AITaskKind.COVER_LETTER.value: handle_cover_letter_result,
    AITaskKind.INTERVIEW_PREP.value: handle_interview_prep_result,
}


def dispatch(task: AITask, raw: str, ctx: "TickContext") -> None:
    handler = _HANDLERS.get(task.kind)
    if handler:
        handler(task, raw, ctx)
    else:
        log.warning("No handler for AITaskKind %s", task.kind)
