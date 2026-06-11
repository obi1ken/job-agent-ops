# Skill: Process AI Outbox (Token-Efficient)

## Purpose
Process pending orchestrator AI tasks (extensions/orchestrator/ai_outbox/) at minimum
token cost. Charles is on a Max plan with a 5-hour rolling window — bulk task
processing must NEVER run at main-session model rates.

## When to invoke
After an orchestrator tick dispatches tasks, or when Charles says "process the outbox".

## How to apply
1. Read extensions/orchestrator/ai_tasks.json and collect tasks with
   status == "AWAITING_OUTPUT".
2. For each task, spawn a SUBAGENT (Agent tool) — do NOT read the prompt file
   into the main session. Prompt files are self-contained (JD text, CV content,
   and output format are all embedded), so subagents need zero project context.
3. Model routing (cost ladder — never use Opus or above for these):
   - SCORE_JD       → model: haiku   (rubric classification)
   - TAILOR_CV      → model: sonnet  (quality writing)
   - COVER_LETTER   → model: sonnet  (quality writing)
   - anything else  → model: sonnet
4. Subagent prompt template:
   "Read <prompt_path>. Follow its instructions exactly. Write your COMPLETE
    response, including the <<<RESULT_JSON>>> ... <<<END>>> block, to
    <output_path> using the Write tool. The file content is consumed by a
    parser — no preamble or commentary outside what the prompt asks for."
5. Spawn independent tasks in parallel (single message, multiple Agent calls).
6. After all subagents finish, verify each output file exists in
   extensions/orchestrator/ai_inbox/ and contains a <<<RESULT_JSON>>> block.
   Re-run failures once; report persistent failures to Charles.
7. The next orchestrator tick consumes the outputs — do not edit ai_tasks.json
   by hand.

## Rules
- Main session NEVER processes prompt-file content itself — orchestration only.
- Respect MAX_NEW_JOBS_PER_TICK (default 3) — if a backlog of >6 tasks exists,
  ask Charles before processing all of them.
- Human-in-loop is untouched: this skill only produces drafts; approval still
  happens in Discord.
