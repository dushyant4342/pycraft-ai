---
description: Generate a commit message and PR description from current git state
allowed-tools: Bash(git diff:*), Bash(git log:*), Bash(git status:*)
---

Generate a commit message and PR description for the current changes. Write this as short as possible.

## Steps

1. Run `git status` to see which files are staged, unstaged, or untracked.
2. Run `git diff HEAD` to get the full diff of all changes.
3. Run `git log --oneline -10` to see recent commit history and match the message style.
4. Based on the above, produce:

**Commit message** (one line, imperative mood, under 72 chars):
```
<type>: <short summary>
```
Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`

**PR description** (markdown):
```
## What
- Bullet points of what changed and why.

## Files changed
- `path/to/file` — one-line reason.

## Test plan
- How to verify the changes work correctly.
```

## Rules
- Match the commit style from `git log` if a convention is already established.
- Keep the commit message to one line; put detail in very short the PR body.
- Do not include untracked files that are clearly not part of the change.
