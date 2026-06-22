# TRACK B — SPICE Verification Harness

Claude Code session, **Track B**, parallel. Read `CLAUDE.md`, `docs/board_spec.md`,
`docs/TESTING_PLAN.md` (Part 1 + report format), and your log `docs/sessions/trackB.md`
(create if absent). Work **only** in your owned paths.

## Owned paths (exclusive write)
`sim/**`, `reports/sim/**`

## Must NOT touch
`hardware/`, `libraries/`, `host/`, `test/`, `scripts/`; shared docs read-only.

## Goal
Build the full ngspice harness and produce the accuracy + noise budget before the board
exists, on a modeled circuit. Parameterize by RTD type and R_ref so it serves whatever
Lucas picks.

## Model strategy
- **CRD:** current source ∥ finite dynamic impedance (MΩ-range for the low-current part) +
  a current-noise source treated as a bound-the-unknown. Make CRD value + tempco sweepable.
- **R_ref:** parameter, with tempco for the budget. **RTD:** swept resistor.
- **Two ADCs:** independent gain terms `G_T7`, `G_ADS` on the V_RTD and V_ref measurements so
  the gain ratio and its tempco can be injected — this is the new accuracy term.

## Deliverables (per TESTING_PLAN Part 1)
- `sim/models/`, `sim/netlists/` decks for: (1) DC op + CRD compliance vs `VL`, (2)
  ratiometric **+ cross-cal** correctness with invariance to ±10 % CRD / R_ref perturbation,
  (3) Monte-Carlo accuracy → **°C error** dominated by R_ref tempco + relative ADC gain
  tempco, (4) R_ref sizing / no-clip vs ADS1115 range, (5) transient RC settling vs mux dwell,
  (6) **ratio noise** combining CRD, Johnson, T7, and ADS1115 noise — explicitly bound CRD
  noise, (7) optional shared-ground crosstalk.
- `sim/scripts/`: ngspice batch runners + python analysis/plots; single `run_all` entry.
- One report per test in `reports/sim/` (TESTING_PLAN skeleton) with explicit pass/fail.

## Done when
- All decks run headless and reproducibly; accuracy budget yields a concrete °C number
  dominated by R_ref + relative gain tempco; ratio-noise test bounds the CRD-noise risk.
- Committed on `trackB`; log updated.

## Coordination
Branch `trackB`, own worktree. Commit; do not merge. Leave a clear hook so **Wave 3** can
re-point decks from the modeled netlist to `sim/netlists/rtd-readout.net` (the KiCad export).
Log to `docs/sessions/trackB.md`.
