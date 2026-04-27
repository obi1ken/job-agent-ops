from .discord_delivery import deliver
from .models import PrepInput, PrepResult, PromptPackage, ResearchTargets
from .prompt_builder import build_prompt
from .research_targets import build_research_targets
from .response_parser import parse_response


class PrepBuilder:
    def prepare(self, prep_input: PrepInput) -> tuple[PromptPackage, ResearchTargets]:
        """Phase 1: build prompt instructions and research query list.

        Caller (orchestrator / Claude Code session) should:
        1. Optionally run the ResearchTargets queries via WebSearch.
        2. If searches were done, call build_final_prompt() to embed results.
        3. Execute the PromptPackage.task_instructions to generate the prep content.
        4. Pass the raw output to finalise().
        """
        package = build_prompt(prep_input)
        targets = build_research_targets(prep_input)
        return package, targets

    def build_final_prompt(self, prep_input: PrepInput, research_results: dict) -> PromptPackage:
        """Rebuild prompt with research results baked in (call after web searches)."""
        return build_prompt(prep_input, research_results=research_results)

    def finalise(self, prep_input: PrepInput, claude_output: str) -> PrepResult:
        """Phase 2: parse Claude Code's output and deliver to Discord."""
        result = parse_response(
            claude_output,
            prep_input.company,
            prep_input.role,
            prep_input.track,
        )
        deliver(result)
        return result
