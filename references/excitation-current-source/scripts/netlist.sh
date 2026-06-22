#!/usr/bin/env bash
# scripts/netlist.sh — export the schematic netlist for SPICE / cross-checks.
# Default output is sim/netlists/<project>.net (the canonical path in
# BOARD_DEV_CHECKLIST.md); override with NETLIST_OUT=/some/path.net.
# Degrades gracefully if no schematic exists yet.
#
# Usage:  scripts/netlist.sh
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/lib/common.sh"

if [ ! -f "$SCH" ]; then
  info "schematic not present ($SCH) — skipping netlist export"
  exit 0
fi

require_kicad_cli || exit 2
mkdir -p "$(dirname "$NETLIST_OUT")"

rc=0
# Default format matches BOARD_DEV_CHECKLIST.md (kicadsexpr). Track B can request a
# SPICE netlist with NETLIST_FORMAT=spice (valid: kicadsexpr, spice, spicemodel, ...).
"$KCLI" sch export netlist \
  --format "${NETLIST_FORMAT:-kicadsexpr}" \
  --output "$NETLIST_OUT" "$SCH" || rc=$?

if [ "$rc" -ne 0 ]; then
  err "netlist export failed (exit $rc)"
else
  ok "netlist exported — $NETLIST_OUT"
  printf '%s\n' "$NETLIST_OUT"
fi
exit "$rc"