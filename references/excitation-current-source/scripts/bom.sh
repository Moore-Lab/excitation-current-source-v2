#!/usr/bin/env bash
# scripts/bom.sh — export the BOM as CSV for review against board_spec.md §7.
# Writes reports/bom/bom_<tag>.csv. Degrades gracefully if no schematic exists yet.
#
# Usage:  scripts/bom.sh [tag]
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/lib/common.sh"

TAG="$(resolve_tag "${1:-}")"
OUT="$BOM_DIR/bom_${TAG}.csv"

if [ ! -f "$SCH" ]; then
  info "schematic not present ($SCH) — skipping BOM export"
  exit 0
fi

require_kicad_cli || exit 2
mkdir -p "$BOM_DIR"

rc=0
"$KCLI" sch export bom \
  --fields "Reference,Value,Footprint,MPN,Manufacturer,Tolerance,Datasheet" \
  --group-by "Value,Footprint" --sort-field Reference --exclude-dnp \
  --output "$OUT" \
  "$SCH" || rc=$?

if [ "$rc" -ne 0 ]; then
  err "BOM export failed (exit $rc)"
else
  ok "BOM exported — $OUT"
  printf '%s\n' "$OUT"
fi
exit "$rc"