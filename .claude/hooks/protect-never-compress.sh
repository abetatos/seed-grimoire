#!/usr/bin/env bash
# PreToolUse hook — protect the NEVER-COMPRESS files from direct edits.
#
# plan/seeds.md and plan/shadow.md are hand-authored, wrapped-field files that
# are the book's only non-regenerable source of truth for foreshadowing and the
# hidden timeline. A load->save round-trip or a careless Edit reflows/drops
# content that no script can rebuild. The rule "mutate these only via
# mark_seed.py / mark_truth.py" lives in CLAUDE.md and two agent definitions as
# prose; this hook makes it structural for the Edit/Write/NotebookEdit tools.
#
# Contract: read the tool-call JSON on stdin, extract the target file path, and
# DENY (exit 2, message on stderr) when it is a never-compress file. Anything
# else exits 0 (allow). The surgical scripts write via Python open(), not the
# Edit tool, so they are unaffected. The author can still edit these files
# outside the agent, or ask the agent to run a script.
#
# Never blocks on its own failure: if the path cannot be parsed, allow (exit 0)
# — this hook is a guardrail against accidents, not a security boundary.

set -uo pipefail

payload="$(cat 2>/dev/null || true)"

file_path="$(
  printf '%s' "$payload" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = data.get("tool_input") or {}
p = ti.get("file_path") or ti.get("notebook_path") or ""
print(p)
' 2>/dev/null || true
)"

case "$file_path" in
  */plan/seeds.md|*/plan/shadow.md|plan/seeds.md|plan/shadow.md)
    echo "BLOCKED: $file_path is a NEVER-COMPRESS file. Do not Edit/Write it directly — a round-trip reflows or drops its wrapped multi-line fields. Advance seed/truth state with the surgical scripts (mark_seed.py / mark_truth.py), or ask the author to make the edit by hand." >&2
    exit 2
    ;;
esac

exit 0
