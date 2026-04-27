from .builder import PrepBuilder
from .models import (
    CvDiffContext,
    PrepInput,
    PrepResult,
    PrepSection,
    PromptPackage,
    ResearchTargets,
)

__all__ = [
    "PrepBuilder",
    "PrepInput",
    "PrepResult",
    "PrepSection",
    "PromptPackage",
    "ResearchTargets",
    "CvDiffContext",
    "run_prep",
]


def run_prep(prep_input: PrepInput, claude_output: str) -> PrepResult:
    """Convenience: parse Claude Code's generated output and deliver to Discord.

    Use when the orchestrator handles phase 1 (prepare + prompt execution) inline
    and just needs to finalise the result.
    """
    return PrepBuilder().finalise(prep_input, claude_output)
