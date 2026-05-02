---
description: Writes and runs tests for a specific pycraft feature. Pass the spec name as argument e.g. /test-feature 05-backend-connection
allowed-tools: Bash(python -m pytest)
---

Run the full testing pipeline for the feature specified in $ARGUMENTS.

If no argument is provided, stop immediately and say:
"Please provide a spec name. Usage: /test-feature <spec-name> e.g. /test-feature"

If `.claude/specs/$ARGUMENTS.md` does not exist, stop immediately and say:
"Spec file not found at .claude/specs/$ARGUMENTS.md. Please check the spec name and try again."


## Final Output

After both subagents complete, produce a combined summary:

### Testing Pipeline Report - $ARGUMENTS

**Step 1 - Tests Written**
- List each test written with a one-line description of which spec requirement it validates

**Step 2 - Test Results**
- Mirror the pycraft-test-runner's structured report

**Verdict**
One of:
- Successfully ready for code review: all tests pass
- Needs fixes: list the failing tests and their root causes