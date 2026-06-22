#!/usr/bin/env bash
# scripts/drc.sh — PCB DRC gate.
# Writes a JSON report to reports/drc/drc_<tag>.json and exits nonzero on violations.
# Degrades gracefully (exit 0) if no PCB exists yet.
#
# Usage:  scripts/drc.sh [tag]          (tag defaults to GATE_TAG or "latest")
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/lib/common.sh"

TAG="$(resolve_tag "${1:-}")"
OUT="$DRC_DIR/drc_${TAG}.json"

if [ ! -f "$PCB" ]; then
  info "PCB not present ($PCB) — skipping DRC"
  exit 0
fi

require_kicad_cli || exit 2
check_kicad_version
mkdir -p "$DRC_DIR"

rc=0
# --refill-zones: refill copper zones before checking so DRC reflects current
# geometry (BOARD_DEV_CHECKLIST.md Phase 3: "Zones refilled before any export").
"$KCLI" pcb drc \
  --exit-code-violations --severity-error --refill-zones \
  --format json --output "$OUT" \
  "$PCB" || rc=$?

if [ "$rc" -ne 0 ]; then
  err "DRC: violations found (exit $rc) — see $OUT"
else
  ok "DRC: clean — $OUT"
fi
printf '%s\n' "$OUT"
exit "$rc"