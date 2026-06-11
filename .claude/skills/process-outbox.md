# Skill: Process AI Outbox (Token-Efficient)

## Purpose
Process pending orchestrator AI tasks (extensions/orchestrator/ai_outbox/) at minimum
token cost. Charles is on a Max plan with a limited 5-hour rolling window — bulk task
processing must NEVER run at main-session model rates.

## Cost model (why batching matters)
Each spawned subagent carries ~10k tokens of fixed harness overhead (system prompt +
tool definitions) before it reads a single prompt file. The task content itself is
small: a score is ~0.6k tokens in+out, a CV tailor ~5.2k, a cover letter ~1.8k.
Per-task agents pay the 10k overhead every time; per-STAGE agents pay it once for
all tasks of that kind. 4 jobs per-task = ~150k; 4 jobs stage-batched = ~60k.

## When to invoke
After an orchestrator tick dispatches tasks, or when Charles says "process the outbox".

## How to apply
1. Read extensions/orchestrator/ai_tasks.json and collect tasks with
   status == "AWAITING_OUTPUT". Group them by kind.
2. Spawn ONE subagent per kind (not per task) — do NOT read prompt files
   into the main session. Prompt files are self-contained (JD text, CV content,
   and output format are all embedded), so subagents need zero project context.
3. Model routing (cost ladder — never use Opus or above for these):
   - SCORE_JD       → model: haiku   (rubric classification)
   - TAILOR_CV      → model: sonnet  (quality writing)
   - COVER_LETTER   → model: sonnet  (quality writing)
   - anything else  → model: sonnet
4. Batched subagent prompt template:
   "Process these prompt files one at a time, fully independently:
    <list of (prompt_path, output_path) pairs>
    For EACH pair: Read the prompt file, follow its instructions exactly, and
    Write your COMPLETE response — including the <<<RESULT_JSON>>> ... <<<END>>>
    block — to its output_path. Finish one file before starting the next.
    Treat each file in isolation: do not let one job's content influence
    another's. The output files are consumed by a parser — no preamble or
    commentary outside what each prompt asks for."
5. Different kinds are independent — spawn their stage-agents in parallel
   (single message, multiple Agent calls) when multiple kinds are pending.
6. After the subagents finish, verify each output file exists in
   extensions/orchestrator/ai_inbox/ and contains a <<<RESULT_JSON>>> block.
   Re-run failures once (individually); report persistent failures to Charles.
7. The next orchestrator tick consumes the outputs — do not edit ai_tasks.json
   by hand.

## Rules
- Main session NEVER processes prompt-file content itself — orchestration only.
- Respect MAX_NEW_JOBS_PER_TICK — if a backlog of >6 tasks exists,
  ask Charles before processing all of them.
- Cap one stage-agent at 8 tasks; split into two agents beyond that
  (output quality degrades on very long runs).
- Human-in-loop is untouched: this skill only produces drafts; approval still
  happens in Discord.
