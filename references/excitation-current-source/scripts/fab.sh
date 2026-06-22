#!/usr/bin/env bash
# scripts/fab.sh — produce a manufacturing drop (gerbers + drill + pos + STEP).
# Output goes to fab/ (gitignored). Per BOARD_DEV_CHECKLIST.md Phase 4 / 3, run this
# ONLY at a tagged, DRC-clean revision so the exact source is recoverable.
#
# This script enforces that intent:
#   - refuses to run unless DRC is clean (override with ALLOW_DIRTY_FAB=1)
#   - warns if the current commit is not tagged (override with ALLOW_UNTAGGED_FAB=1)
#
# Usage:  scripts/fab.sh [tag]
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/lib/common.sh"

TAG="$(resolve_tag "${1:-}")"

if [ ! -f "$PCB" ]; then
  err "PCB not present ($PCB) — cannot produce a fab drop"
  exit 2
fi

require_kicad_cli || exit 2
check_kicad_version

# Gate the drop on a clean DRC unless explicitly overridden.
if [ "${ALLOW_DIRTY_FAB:-0}" != "1" ]; then
  if ! "$SCRIPT_DIR/drc.sh" "$TAG" >/dev/null; then
    err "DRC is not clean — refusing to cut a fab drop. (set ALLOW_DIRTY_FAB=1 to override)"
    exit 1
  fi
fi

# Warn if HEAD is not on a git tag (releases should be tagged, e.g. rev-A).
if [ "${ALLOW_UNTAGGED_FAB:-0}" != "1" ]; then
  if ! git -C "$REPO_ROOT" describe --exact-match --tags HEAD >/dev/null 2>&1; then
    warn "HEAD is not tagged — fab drops should be cut at a tagged rev (see DIRECTORY_MANAGEMENT.md)."
    warn "  tag first, e.g.: git tag rev-A   (or set ALLOW_UNTAGGED_FAB=1 to proceed anyway)"
  fi
fi

mkdir -p "$FAB_DIR/gerbers" "$FAB_DIR/drill" "$FAB_DIR/pos"

rc=0
info "exporting gerbers..."
"$KCLI" pcb export gerbers --output "$FAB_DIR/gerbers/" "$PCB" || rc=$?
info "exporting drill files..."
"$KCLI" pcb export drill   --output "$FAB_DIR/drill/"   "$PCB" || rc=$?
info "exporting placement (pos)..."
"$KCLI" pcb export pos     --output "$FAB_DIR/pos/"     "$PCB" || rc=$?
info "exporting STEP model..."
"$KCLI" pcb export step --force --output "$FAB_DIR/$PROJECT.step" "$PCB" || rc=$?

if [ "$rc" -ne 0 ]; then
  err "fab export had failures (last exit $rc) — inspect $FAB_DIR"
else
  ok "fab drop written to $FAB_DIR (gerbers/ drill/ pos/ $PROJECT.step)"
  warn "fab/ is gitignored — capture this drop with a git tag (e.g. git tag fab-rev-A)."
fi
exit "$rc"