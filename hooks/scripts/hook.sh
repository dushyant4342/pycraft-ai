#!/bin/bash
PLUGIN_HOOK="C:/Users/dushyant/.claude/plugins/cache/agents-observe/agents-observe/0.9.2/hooks/scripts/hook.sh"
if [ -f "$PLUGIN_HOOK" ]; then
  exec bash "$PLUGIN_HOOK"
fi
exit 0
