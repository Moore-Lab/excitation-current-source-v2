#!/usr/bin/env bash
# scripts/lib/common.sh — shared helpers for the Track D gate/automation scripts.
#
# Source this from a wrapper:  . "$(dirname "$0")/lib/common.sh"
# It defines repo paths, locates kicad-cli portably, and provides logging helpers.
# It does NOT call `set -e` — each wrapper decides its own error policy because the
# gate tools intentionally exit nonzero on violations and we must capture that.

# ---------------------------------------------------------------------------
# Repo paths
# ---------------------------------------------------------------------------
# Prefer git's idea of the root; fall back to the directory two levels above this
# file (scripts/lib/common.sh -> repo root) when run outside a git checkout.
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$REPO_ROOT" ]; then
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi
export REPO_ROOT

# Project base name (kept consistent across .kicad_pro/.sch/.pcb — see
# docs/DIRECTORY_MANAGEMENT.md). Override with PROJECT=... if it ever changes.
PROJECT="${PROJECT:-ref200-rtd}"

HW_DIR="$REPO_ROOT/hardware"
# SCH/PCB default to the canonical project files but are overridable (handy for
# validating a file at a non-standard path, or for testing the scripts).
SCH="${SCH:-$HW_DIR/$PROJECT.kicad_sch}"
PCB="${PCB:-$HW_DIR/$PROJECT.kicad_pcb}"

# Generated-artifact destinations (committed, except fab/ which is gitignored).
ERC_DIR="$REPO_ROOT/reports/erc"
DRC_DIR="$REPO_ROOT/reports/drc"
BOM_DIR="$REPO_ROOT/reports/bom"
NETLIST_OUT="${NETLIST_OUT:-$REPO_ROOT/sim/netlists/$PROJECT.net}"
FAB_DIR="${FAB_DIR:-$REPO_ROOT/fab}"

# Pinned KiCad major.minor (full pin is 10.0.3 — see docs/SESSION_LOG.md).
KICAD_PIN="${KICAD_PIN:-10.0}"

# ---------------------------------------------------------------------------
# Logging (to stderr so report paths printed on stdout stay clean)
# ---------------------------------------------------------------------------
info() { printf '  %s\n' "$*" >&2; }
ok()   { printf '  [ok]  %s\n' "$*" >&2; }
warn() { printf '  [warn] %s\n' "$*" >&2; }
err()  { printf '  [err] %s\n' "$*" >&2; }

# ---------------------------------------------------------------------------
# Locate kicad-cli
# ---------------------------------------------------------------------------
# Order: explicit KICAD_CLI env -> on PATH -> known Windows install dirs.
# Prints the resolved path on stdout and returns 0, or returns 1 if not found.
find_kicad_cli() {
  if [ -n "${KICAD_CLI:-}" ] && [ -x "$KICAD_CLI" ]; then
    printf '%s\n' "$KICAD_CLI"; return 0
  fi
  if command -v kicad-cli >/dev/null 2>&1; then
    command -v kicad-cli; return 0
  fi
  local p
  for p in \
    "/c/Program Files/KiCad/10.0/bin/kicad-cli.exe" \
    "/c/Program Files/KiCad/9.0/bin/kicad-cli.exe" \
    "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" \
    "C:/Program Files/KiCad/9.0/bin/kicad-cli.exe"; do
    if [ -x "$p" ]; then printf '%s\n' "$p"; return 0; fi
  done
  return 1
}

# Resolve kicad-cli into the KCLI variable or fail with a clear message.
# Usage: require_kicad_cli || return 2   (or exit 2 from a top-level script)
require_kicad_cli() {
  KCLI="$(find_kicad_cli)" || {
    err "kicad-cli not found. Install KiCad ${KICAD_PIN}.x, or set KICAD_CLI=/path/to/kicad-cli."
    return 1
  }
  export KCLI
  return 0
}

# Soft version check: warn (do not fail) if the running kicad-cli is not the pinned
# major.minor. A major bump can rewrite the .kicad_* file formats (see kickoff).
check_kicad_version() {
  local ver
  ver="$("$KCLI" version 2>/dev/null | head -1)"
  case "$ver" in
    "$KICAD_PIN".*) : ;;  # matches pin
    "") warn "could not read kicad-cli version" ;;
    *)  warn "kicad-cli is $ver but project pins ${KICAD_PIN}.x — file formats may differ" ;;
  esac
}

# Resolve the report tag: first positional arg, else GATE_TAG env, else "latest".
# Reports are named with this tag, e.g. erc_s002.json (session id) per
# docs/DIRECTORY_MANAGEMENT.md. Sanitize to keep filenames safe.
resolve_tag() {
  local t="${1:-${GATE_TAG:-latest}}"
  # No trailing newline into tr, or the newline itself becomes a "_".
  printf '%s' "$t" | tr -c 'A-Za-z0-9._-' '_'
}