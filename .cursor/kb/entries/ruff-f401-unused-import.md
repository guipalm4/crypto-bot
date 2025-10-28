---
id: ruff-f401-unused-import
title: Ruff F401 - unused import
tags: [ruff, lint, imports]
owner: maintainers
createdAt: 2025-10-28
updatedAt: 2025-10-28
resolutionLevel: approved
appliesTo:
  paths: ["**/*.py"]
  tools: ["ruff"]
patterns:
  - "F401\\b.*unused import"
  - "unused import\\b"
links:
  taskmaster: []
  prs: []
  commits: []
---

## Symptoms
- Ruff reports `F401: <name> imported but unused`.

## Root Cause
- Symbol imported but not referenced in the module. Often leftover from refactors or re-exports not needed.

## Standard Resolution
1. Remove the unused import line.
2. If the import is needed for side-effects or public API exposure, add `# noqa: F401` with a comment explaining why, or prefer an explicit `__all__` export pattern.
3. For tests, consider narrowing imports to the specific used symbols.

## Code Diff Guidance
- Remove lines like:
  - `from x import y  # unused`
  - `import x  # unused`
- If side-effect is required, prefer:
  - Add a short comment: `# required side-effect (register signals)` and optionally `# noqa: F401`.

## Validation
- Run:
  - `ruff check --config=pyproject.toml .`
- Ensure no F401 remains.

## Notes
- Avoid blanket `noqa` unless justified.
- Prefer keeping imports close to usage sites.

