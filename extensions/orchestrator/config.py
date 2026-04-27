from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class ScoringThresholds:
    default_apply: float
    track_d_apply: float
    priority_flag: float
    urgent_flag: float

    def threshold_for(self, track: str) -> float:
        return self.track_d_apply if track.upper() == "D" else self.default_apply


@dataclass
class ProfileConfig:
    project_root: Path
    candidate_full_name: str
    candidate_email: str
    scoring: ScoringThresholds

    # Derived paths
    applications_md_path: Path
    cv_master_path: Path
    portals_yml_path: Path

    # Orchestrator working dirs
    orchestrator_dir: Path      # extensions/orchestrator/
    ai_outbox_dir: Path         # extensions/orchestrator/ai_outbox/
    ai_inbox_dir: Path          # extensions/orchestrator/ai_inbox/
    output_dir: Path            # output/
    jds_dir: Path               # jds/


def load_profile(project_root: str | None = None) -> ProfileConfig:
    root = Path(project_root or os.environ.get("PROJECT_ROOT", ".")).resolve()
    yml_path = root / "config" / "profile.yml"
    if not yml_path.exists():
        raise FileNotFoundError(f"profile.yml not found at {yml_path}")

    with yml_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    candidate = data.get("candidate", {})
    thresholds = data.get("scoring_thresholds", {})

    orch_dir = root / "extensions" / "orchestrator"

    return ProfileConfig(
        project_root=root,
        candidate_full_name=candidate.get("full_name", ""),
        candidate_email=candidate.get("email", ""),
        scoring=ScoringThresholds(
            default_apply=float(thresholds.get("default_apply", 3.5)),
            track_d_apply=float(thresholds.get("track_D_apply", 3.0)),
            priority_flag=float(thresholds.get("priority_flag", 4.0)),
            urgent_flag=float(thresholds.get("urgent_flag", 4.5)),
        ),
        applications_md_path=root / "data" / "applications.md",
        cv_master_path=root / "cv.md",
        portals_yml_path=root / "portals.yml",
        orchestrator_dir=orch_dir,
        ai_outbox_dir=orch_dir / "ai_outbox",
        ai_inbox_dir=orch_dir / "ai_inbox",
        output_dir=root / "output",
        jds_dir=root / "jds",
    )
