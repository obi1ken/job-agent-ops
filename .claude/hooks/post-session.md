# Hook: post-session

## Trigger
End of any session where 5+ project files were written, or Charles says "update hot".

## Purpose
Keep wiki/hot.md current so the next session starts with accurate context.

## What to update in hot.md
1. What shipped this session (files created, decisions made)
2. What is in progress (partially complete items)
3. What is queued next (next concrete actions)
4. Any open decisions carried forward

## Format
Keep under 500 words. Terse. No fluff.
Use the existing hot.md structure as template.

## Windows Note
This file is .md only. No .sh equivalent exists in this directory.
Trigger is manual (Charles says "update hot") or agent-initiated after 5+ writes.
