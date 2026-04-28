---
description: Generate a structured feature spec file for PyCraft AI and save it to .claude/specs/
allowed-tools: Read, Write, Glob
---

Create a spec file for: $ARGUMENTS

## Steps

1. Read `.claude/CLAUDE.md` for project rules and stack constraints.
2. Glob `.claude/specs/*.md` to find existing specs; read them to understand conventions and avoid overlap.
3. Set the next spec number (count existing files + 1, zero-padded to 2 digits).
4. Write the spec to `.claude/specs/<NN>-<kebab-feature-name>.md` using this structure:

```
# Spec <NN>: <Feature Title>

## Goal
What problem this solves and why it belongs in PyCraft AI.

## Files
Each file to create or modify, with a one-line description.

## Design
Key decisions, data flow, or algorithm. Include signatures, data structures, or schema changes.

## Functions / Classes
| Name | Signature | Returns | Notes |

## Constraints
Hard rules this implementation must obey.

## Acceptance Criteria
Concrete, testable conditions that define "done".
```
