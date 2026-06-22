#!/usr/bin/env bash
# Stop hook — per-chapter /clear reminder.
#
# The project standard is: one chapter per session, then /clear. Several
# heavy steps drop a sentinel file (notes/.clear-pending) when they finish:
#   - update-canon (chapter locked)
#   - critique-plan (plan audited — re-audit fresh after edits)
# This hook fires on agent stop, and if the sentinel exists it reminds the
# author to /clear, then consumes the sentinel so the reminder shows exactly
# once (not on every turn).
#
# The sentinel may carry its OWN reminder text: if the file is non-empty, its
# content is used verbatim as the message (so each step says the right thing).
# If empty (e.g. a bare `touch` from update-canon), the default chapter
# message is used.
#
# Output contract: emit nothing on the common case; emit a single JSON
# object with `systemMessage` when a sentinel was found. Always exit 0 so the
# Stop flow is never blocked.

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
sentinel="$(find "$root/output" -name .clear-pending 2>/dev/null | head -1 || true)"

if [ -n "$sentinel" ]; then
  msg="$(cat "$sentinel" 2>/dev/null || true)"
  rm -f "$sentinel" || true
  if [ -z "${msg//[[:space:]]/}" ]; then
    msg="✅ Capítulo bloqueado en canon. ESTÁNDAR: ejecuta /clear y reentra con resume-act antes del próximo capítulo (un capítulo por sesión)."
  fi
  # JSON-escape the message (backslashes and double quotes) for safe embedding.
  msg="${msg//\\/\\\\}"
  msg="${msg//\"/\\\"}"
  printf '{"systemMessage":"%s"}' "$msg"
fi

exit 0
