from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CvDiffContext:
    """Subset of DiffEntry passed from cv_diff extension — avoids cross-extension import."""
    track: str
    keywords_injected: list[str] = field(default_factory=list)
    keywords_removed: list[str] = field(default_factory=list)


@dataclass
class PrepInput:
    jd_text: str
    company: str
    role: str
    track: str                              # "A" | "B" | "C" | "D"
    cv_diff: Optional[CvDiffContext] = None


@dataclass
class ResearchTargets:
    queries: list[str]


@dataclass
class PromptPackage:
    task_instructions: str
    token_estimate: int


@dataclass
class PrepSection:
    name: str
    content: str


@dataclass
class PrepResult:
    company: str
    role: str
    track: str
    sections: list[PrepSection]
    timestamp_utc: str
