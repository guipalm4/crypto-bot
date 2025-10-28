---
id: <unique-id>
title: <short-title>
tags: [tool, category]
owner: <maintainer>
createdAt: <YYYY-MM-DD>
updatedAt: <YYYY-MM-DD>
resolutionLevel: experimental
appliesTo:
  paths: ["**/*.py"]
  tools: ["ruff", "mypy", "pytest"]
patterns:
  - "<regex capturing error text>"
links:
  taskmaster: ["<task-id>"]
  prs: ["<url>"]
  commits: ["<sha>"]
---

## Symptoms
- <error messages or stack traces>

## Root Cause
- <concise diagnosis>

## Standard Resolution
1. <step-by-step resolution>

## Code Diff Guidance
- <concise guidance; avoid long blobs>

## Validation
- Run commands to verify (e.g., ruff/mypy/pytest)

## Notes
- Security/Performance caveats

