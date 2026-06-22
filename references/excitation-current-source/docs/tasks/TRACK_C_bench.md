# TRACK C — Bench Procedures & T7 Control

You are a Claude Code session working **Track C** in parallel with others. Read
`CLAUDE.md`, `docs/board_spec.md` (esp. §5 AIN modes, §6 wiring), `docs/TESTING_PLAN.md`
(Part 2 + report format), and your track log `docs/sessions/trackC.md` (create if absent).
Work **only** within your owned paths.

## Owned paths (exclusive write)
`test/**`

## Must NOT touch
`hardware/`, `libraries/`, `sim/`, `scripts/`, shared docs (read-only).

## Goal
Write the bench bring-up procedures and the LabJack T7 Pro control/data-logging code so
that the moment the physical board exists, Lucas can run the staged tests with no glue work
left to do. No hardware is needed to write and lint this.

## Deliverables (per `TESTING_PLAN.md` Part 2)
- `test/procedures/`: a runnable script per stage (0 power-off checks → 8 thermal soak).
  Critical ones:
  - **Stage 2** current verification + per-channel calibration capture (writes each
    channel's measured current as the calibration constant for calibrated-current mode).
  - **Stage 3** ratiometric accuracy via substituted precision resistors / decade box,
    computing `R_ref·V_RTD/V_ref`.
  - **Stage 6** noise + **position-independence** comparison — the headline acceptance
    test; include tooling to load the old series-chain data and compare directly.
- T7 control via LJM: per-channel reads of V_ref and V_RTD on the correct AIN range
  (Pt100 ±0.1 V, Pt1000 ±1 V), differential or single-ended-subtract per the chosen AIN
  mode, with configurable settling/resolution index (guard against the mux-settling risk).
- Data schema + logging into `test/data/` (committed — irreplaceable). Report templates
  wired to the `TESTING_PLAN.md` skeleton, output to `reports/test/` at run time.

## Done when
- All stage scripts written, import/lint clean, and dry-run against synthetic/mock T7 data
  (no hardware) without errors.
- Parameterized for Pt100 and Pt1000 so the RTD-type decision doesn't require a rewrite.
- Committed on branch `trackC`; track log updated.

## Coordination
Branch `trackC`, own worktree. Commit; do not merge. Independent of all other Wave-0
tracks. Log to `docs/sessions/trackC.md`.
