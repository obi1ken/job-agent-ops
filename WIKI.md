# WIKI.md — Schema and Governance Rules
# Job Agent Ops wiki system (Karpathy pattern)
# Generated: 2026-04-24

---

## Directory Structure

raw/          Source-of-truth files. Authoritative over wiki/.
              Never synthesised or interpreted — raw inputs only.

wiki/
  hot.md      Rolling session context (~500 words max).
              Read FIRST at every session start.
  index.md    One-line summary per page, grouped by category.
              Updated on every ingest.
  log.md      Append-only event log. One line per event.
  pages/      All wiki pages live here.

---

## Staleness Rules

- A page is stale ONLY if a file listed in its `sources:` frontmatter
  has been modified (mtime) since the page's `last_verified` date.
- No time backstop — a page does not go stale just because time passed
  if its sources have not changed.
- Check staleness by comparing file mtime of each source against
  the page's last_verified field.

---

## Contradiction Handling

When a contradiction is detected between sources or between a source
and a wiki page:

1. Add an inline warning block to the affected page:
   > **CONTRADICTION:** <description of conflict between source A and source B>

2. Add a log entry to wiki/log.md:
   YYYY-MM-DD: CONTRADICTION — <page> — <brief description>

3. Add `contradiction: <source-ref>` to the page frontmatter.

4. Do NOT flip page status to stale on contradiction alone.
   Status stays current. Contradiction is flagged inline.

5. Resolve contradictions by asking Charles — do not silently pick one source.

---

## Page Frontmatter Schema

Every page in wiki/pages/ MUST have this frontmatter:

```yaml
---
status: current | stale | deprecated | planned
last_updated: YYYY-MM-DD
last_verified: YYYY-MM-DD
sources:
  - raw/filename.md
  - raw/filename2.md
synthesis: one-line description of what sources this page bridges
contradiction: <source-ref>   # optional — only if contradiction exists
---
```

Status definitions:
- current    — page reflects sources as of last_verified
- stale      — one or more sources modified since last_verified
- deprecated — page no longer needed; kept for history
- planned    — page outline only; not yet written

---

## Log Granularity

Record in wiki/log.md:
  - Ingests (new raw files added)
  - Lint runs
  - Structural changes (pages added, deprecated, renamed)
  - Contradictions detected

Do NOT record:
  - Typo fixes
  - Minor wording edits
  - Routine stub expansions

Format: YYYY-MM-DD: [event description]

---

## hot.md Rules

- Maximum ~500 words
- Content: what is in progress, what just shipped, what is queued next
- Update triggers:
    1. Charles says "update hot"
    2. 5+ project files written in a single session
- Read hot.md BEFORE anything else at session start

---

## Bootstrap Protocol

Phase 1 (proposal): propose skeleton page list to Charles for approval.
Phase 2 (execution): create stub pages only — 5-line stubs with valid
frontmatter + 1-line summary + source pointer + TODO list. Expand lazily on demand.

---

## raw/ Authoritative Rule

raw/ files are always more authoritative than wiki/ pages.
If a wiki page contradicts its raw/ source, the raw/ source wins.
Flag the contradiction per the rules above rather than silently updating.
