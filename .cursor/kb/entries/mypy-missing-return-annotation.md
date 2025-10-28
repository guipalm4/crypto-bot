---
id: mypy-missing-return-annotation
title: MyPy - Function missing return type annotation
tags: [mypy, types]
owner: maintainers
createdAt: 2025-10-28
updatedAt: 2025-10-28
resolutionLevel: approved
appliesTo:
  paths: ["src/**/*.py", "tests/**/*.py"]
  tools: ["mypy"]
patterns:
  - "error: Function is missing a type annotation for return value"
  - "Missing return type annotation"
links:
  taskmaster: []
  prs: []
  commits: []
---

## Symptoms
- MyPy reports a function or method without explicit return type annotation.

## Root Cause
- Missing `-> ReturnType` in the function signature.

## Standard Resolution
1. Add an explicit return type to the function signature:
   - Example: `def load_config(path: str) -> dict[str, Any]: ...`
2. Prefer concrete types (e.g., `dict[str, Any]`, `list[Item]`) over `Any`.
3. For async functions, annotate with `-> T` (not `Coroutine`) unless low-level.
4. If function returns `None`, annotate `-> None`.
5. If the function is intentionally dynamic, add precise `typing` aliases or `Protocol`.

## Code Diff Guidance
- Update signatures only; avoid adding runtime casts just to satisfy types.
- If needed, add imports from `typing` (e.g., `from typing import Any, Optional, Protocol`).

## Validation
- Run:
  - `mypy src/crypto_bot`
- Ensure no MyPy errors remain for the function.

## Notes
- Align with `pyproject.toml` MyPy settings (strict equality, no implicit optional, etc.).

