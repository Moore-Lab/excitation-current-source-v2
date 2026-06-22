#!/usr/bin/env bash
# scripts/erc.sh — schematic ERC gate.
# Writes a JSON report to reports/erc/erc_<tag>.json and exits nonzero on errors.
# Degrades gracefully (exit 0) if no schematic exists yet.
#
# Usage:  scripts/erc.sh [tag]          (tag defaults to GATE_TAG or "latest")
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/lib/common.sh"

TAG="$(resolve_tag "${1:-}")"
OUT="$ERC_DIR/erc_${TAG}.json"

if [ ! -f "$SCH" ]; then
  info "schematic not present ($SCH) — skipping ERC"
  exit 0
fi

require_kicad_cli || exit 2
check_kicad_version
mkdir -p "$ERC_DIR"

rc=0
"$KCLI" sch erc \
  --exit-code-violations --severity-error \
  --format json --output "$OUT" \
  "$SCH" || rc=$?

if [ "$rc" -ne 0 ]; then
  err "ERC: violations found (exit $rc) — see $OUT"
else
  ok "ERC: clean — $OUT"
fi
printf '%s\n' "$OUT"
exit "$rc"