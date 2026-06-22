#!/usr/bin/env bash
# Stop hook — per-chapter /clear reminder.
#
# The project standard is: one chapter per session, then /clear. When
# `update-canon` locks a chapter it drops a sentinel file
# (notes/.clear-pending). This hook fires on agent stop, and if the
# sentinel exists it reminds the author to /clear, then consumes the
# sentinel so the reminder shows exactly once (not on every turn).
#
# Output contract: emit nothing on the common case; emit a single JSON
# object with `systemMessage` when a chapter was just locked. Always
# exit 0 so the Stop flow is never blocked.

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
sentinel="$(find "$root/output" -name .clear-pending 2>/dev/null | head -1 || true)"

if [ -n "$sentinel" ]; then
  rm -f "$sentinel" || true
  printf '%s' '{"systemMessage":"✅ Capítulo bloqueado en canon. ESTÁNDAR: ejecuta /clear y reentra con resume-act antes del próximo capítulo (un capítulo por sesión)."}'
fi

exit 0
