# TRACK D — Automation, Gates & Repo Meta

You are a Claude Code session working **Track D** in parallel with others. Read
`CLAUDE.md`, `docs/BOARD_DEV_CHECKLIST.md` (canonical gate commands),
`docs/DIRECTORY_MANAGEMENT.md`, and your track log `docs/sessions/trackD.md` (create if
absent). Work **only** within your owned paths.

## Owned paths (exclusive write)
`scripts/**`, `reports/erc/`, `reports/drc/`, `.gitignore`, `README.md`

## Must NOT touch
`hardware/` contents, `libraries/`, `sim/`, `test/`, the other process docs (read-only).

## Goal
Build the automation that turns the checklist's gate commands into one-command, machine-
checkable steps, so every other session and the integration step can validate cheaply and
identically.

## Deliverables
- `scripts/` wrappers for the canonical `kicad-cli` gates in `BOARD_DEV_CHECKLIST.md`:
  ERC, DRC (both with `--exit-code-violations --severity-error`), BOM export, netlist
  export, and the tagged fab drop (gerbers/drill/pos/step).
- A single `scripts/run_gates` entry point that runs ERC + DRC, writes JSON reports to
  `reports/erc|drc/`, and returns nonzero on any error. It must **degrade gracefully** when
  `hardware/*.kicad_sch|pcb` don't exist yet (report "not present", exit 0) so it's usable
  before Track E lands.
- `.gitignore` per `DIRECTORY_MANAGEMENT.md` (KiCad backups/local, `fab/`, python, sim
  scratch). Confirm `*.kicad_pro` stays tracked and `*.kicad_prl` is ignored.
- `README.md`: project overview, toolchain + pinned KiCad version, how to run gates, how to
  produce a fab drop, and a pointer to `docs/PARALLEL_PLAN.md`.
- Optional: a KiCad `jobset` and/or a pre-commit hook enforcing ERC/DRC-clean.

## Done when
- `scripts/run_gates` runs end-to-end today (no KiCad files yet → clean "nothing to check"
  exit) and is ready to enforce gates once schematic/PCB appear.
- All wrappers documented in the README.
- Committed on branch `trackD`; track log updated.

## Coordination
Branch `trackD`, own worktree. Commit; do not merge. Your scripts *reference* `hardware/`
paths but never edit KiCad files. Log to `docs/sessions/trackD.md`.
