# Command: /lint-wiki

Lint the wiki for staleness, missing frontmatter, and broken source references.

## Usage
/lint-wiki

## What it does
1. Reads wiki/index.md to get all registered pages
2. For each page in wiki/pages/: checks frontmatter is complete and valid
3. Checks each file in sources: frontmatter exists in raw/
4. Compares source file mtime against page last_verified — flags stale pages
5. Reports any pages missing from index.md
6. Reports any pages with missing or invalid status values
7. Logs lint run to wiki/log.md

## Output
- List of stale pages with which source changed
- List of pages with missing frontmatter fields
- List of broken source references
- Summary: N pages OK, M stale, P errors
