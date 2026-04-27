# Hook: pre-apply

## Trigger
Before any application submission action.

## Purpose
Enforce the human-in-loop review gate. Nothing submits to any employer without
Charles's explicit approval.

## Rule (NON-NEGOTIABLE)
STOP before submitting. Present the following to Charles for review:
1. The tailored CV variant
2. The cover letter
3. The job URL and company name
4. The track selected and score
5. Any flags (Track D EDMS match, Track C rail keyword boost, legitimacy concerns)

Only proceed after Charles gives explicit approval (in chat or via Discord in Phase 2).

## Windows Note
This file is .md only. No .sh equivalent exists in this directory.
Actual enforcement is via agent instruction (this file) and Phase 2 Discord approval gate.
