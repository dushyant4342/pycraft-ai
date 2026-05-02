---
name: "pycraft-test-runner"
description: "Always invoke after the test-writer subagent completes"
tools: Glob, Grep, Read, TaskStop, WebFetch, WebSearch
model: sonnet
color: cyan
---

agent when pytest tests for a pycraft feature have already been written and need to be executed and analyzed. NEVER invoke before test files exist. Always invoke after the test-writer subagent completes."
