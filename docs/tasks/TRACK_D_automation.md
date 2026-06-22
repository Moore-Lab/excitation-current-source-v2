# TRACK D — Automation, Gates & Repo Meta

Claude Code session, **Track D**, parallel. Read `CLAUDE.md`, `docs/BOARD_DEV_CHECKLIST.md`
(canonical gate commands), `docs/DIRECTORY_MANAGEMENT.md`, and your log
`docs/sessions/trackD.md` (create if absent). Work **only** in your owned paths.

## Owned paths (exclusive write)
`scripts/**`, `reports/erc/`, `reports/drc/`, `reports/bom/`, `.gitignore`, `README.md`

## Must NOT touch
`hardware/` contents, `libraries/`, `sim/`, `host/`, `test/`; other process docs read-only.

## Goal
Turn the checklist's gate commands into one-command, machine-checkable steps so every other
session and the integration step validate identically and cheaply.

## Deliverables
- `scripts/` wrappers for the canonical `kicad-cli` gates: ERC, DRC (both
  `--exit-code-violations --severity-error`), BOM export (include `Tempco` field), netlist
  export, and the tagged fab drop (gerbers/drill/pos/step).
- A single `scripts/run_gates` entry point: runs ERC + DRC, writes JSON to
  `reports/{erc,drc}/`, returns nonzero on any error, and **degrades gracefully** when
  `hardware/*.kicad_sch|pcb` don't exist yet (report "not present", exit 0) so it's usable
  before Track E lands.
- `.gitignore` per `DIRECTORY_MANAGEMENT.md` (KiCad local/backups, `fab/`, python, sim
  scratch); confirm `*.kicad_pro` tracked, `*.kicad_prl` ignored.
- `README.md`: overview of the architecture (CRD + R_ref + T7 V_RTD + I²C ADS1115 V_ref,
  live ratiometric), pinned KiCad version, how to run gates, how to cut a fab drop, pointer
  to `docs/PARALLEL_PLAN.md`.
- Optional: a KiCad `jobset` and/or a pre-commit hook enforcing ERC/DRC-clean.

## Done when
- `scripts/run_gates` runs end-to-end today (no KiCad files → clean "nothing to check"
  exit) and is ready to enforce gates once schematic/PCB appear; wrappers documented in
  the README.
- Committed on `trackD`; log updated.

## Coordination
Branch `trackD`, own worktree. Commit; do not merge. Scripts *reference* `hardware/` paths
but never edit KiCad files. Log to `docs/sessions/trackD.md`.
