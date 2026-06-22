#!/usr/bin/env sh
# scripts/lib.sh — shared helpers for the RTD-readout gate/automation scripts.
#
# Sourced (not executed) by the runnable wrappers: run_gates, erc, drc,
# export_bom, export_netlist, fab_drop. The caller must set REPO_ROOT first.
# Convention in scripts/: sourced libraries end in .sh; runnable commands have
# no extension and a shebang (invoke as `sh scripts/<name>` or `./scripts/<name>`).

# --- Pinned toolchain (docs/SESSION_KICKOFF.md step 4) -----------------------
# Bump deliberately: a KiCad major bump can rewrite the .kicad_* file formats.
KICAD_PINNED="10.0.3"

# --- Board / path constants (docs/DIRECTORY_MANAGEMENT.md §Naming) -----------
BOARD_BASENAME="rtd-readout"
HW_DIR="$REPO_ROOT/hardware"
SCH_FILE="$HW_DIR/${BOARD_BASENAME}.kicad_sch"
PCB_FILE="$HW_DIR/${BOARD_BASENAME}.kicad_pcb"

# Output dirs default under reports/ but honor a pre-set env value (fab_drop
# reuses export_bom by pointing BOM_DIR at fab/bom).
ERC_DIR="${ERC_DIR:-$REPO_ROOT/reports/erc}"
DRC_DIR="${DRC_DIR:-$REPO_ROOT/reports/drc}"
BOM_DIR="${BOM_DIR:-$REPO_ROOT/reports/bom}"
NETLIST_DIR="${NETLIST_DIR:-$REPO_ROOT/sim/netlists}"   # Track B's tree; written only at run time
FAB_DIR="${FAB_DIR:-$REPO_ROOT/fab}"                    # gitignored; cut only at a tagged rev

# --- Logging (all to stderr so report paths on stdout stay parseable) --------
log()  { printf '%s\n'   "$*" >&2; }
info() { printf '  %s\n' "$*" >&2; }
err()  { printf 'ERROR: %s\n' "$*" >&2; }

# --- kicad-cli discovery -----------------------------------------------------
# Order: $KICAD_CLI override -> PATH -> known Windows install dirs (Git Bash).
find_kicad_cli() {
  if [ -n "${KICAD_CLI:-}" ]; then
    [ -x "$KICAD_CLI" ] && { printf '%s\n' "$KICAD_CLI"; return 0; }
    err "KICAD_CLI is set to '$KICAD_CLI' but it is not executable"
    return 1
  fi
  if command -v kicad-cli >/dev/null 2>&1; then
    command -v kicad-cli
    return 0
  fi
  for p in "/c/Program Files/KiCad"/*/bin/kicad-cli.exe \
           "/c/Program Files (x86)/KiCad"/*/bin/kicad-cli.exe; do
    [ -x "$p" ] && { printf '%s\n' "$p"; return 0; }
  done
  return 1
}

# Resolve once. Callers use "$KICAD" and gate on kicad_ok.
KICAD="$(find_kicad_cli 2>/dev/null || true)"
kicad_ok() { [ -n "$KICAD" ] && [ -x "$KICAD" ]; }

kicad_version() {
  kicad_ok || return 1
  "$KICAD" version 2>/dev/null | head -1
}

# Warn (do not fail) if the installed kicad-cli differs from the pinned version.
check_kicad_version() {
  _v="$(kicad_version || true)"
  [ -n "$_v" ] || return 0
  case "$_v" in
    "$KICAD_PINNED") : ;;
    *) log "WARNING: kicad-cli $_v != pinned $KICAD_PINNED — note any format-affecting bump in the log" ;;
  esac
}

# --- Report helpers ----------------------------------------------------------
# Tag stamps report filenames; default 'latest' overwrites for clean git diffs.
# Override per run with `--tag s007` (run_gates) or RTD_GATE_TAG in the env.
gate_tag() { printf '%s' "${RTD_GATE_TAG:-latest}"; }

# Indicative severity tally for the human summary only — the line-count ASSUMES
# KiCad's pretty-printed JSON (one "severity" field per line), which 10.0.3
# emits. It is deliberately not a real JSON parse (no jq dependency); if a future
# KiCad minifies the report this under-counts. That is acceptable because the
# pass/fail signal is the gate's --exit-code-violations exit code, never this.
count_severity() { # <json-file> <severity>
  [ -f "$1" ] || { printf '0'; return; }
  printf '%s' "$(grep -c "\"severity\"[[:space:]]*:[[:space:]]*\"$2\"" "$1" 2>/dev/null || printf 0)"
}