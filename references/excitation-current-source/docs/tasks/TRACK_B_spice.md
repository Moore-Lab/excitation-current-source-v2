# TRACK B — SPICE Verification Harness

You are a Claude Code session working **Track B** in parallel with others. Read
`CLAUDE.md`, `docs/board_spec.md`, `docs/TESTING_PLAN.md` (Part 1 + report format), and
your track log `docs/sessions/trackB.md` (create if absent). Work **only** within your
owned paths.

## Owned paths (exclusive write)
`sim/**`, `reports/sim/**`

## Must NOT touch
`hardware/`, `libraries/`, `test/`, `scripts/`, shared docs (read-only).

## Goal
Build the full ngspice test harness and produce the accuracy + noise budget **before**
the board exists, using a modeled circuit. Parameterize by RTD type and R_ref so it serves
whatever Lucas picks (Pt100/100 Ω/200 µA or Pt1000/1 kΩ/100 µA).

## Deliverables (per `TESTING_PLAN.md` Part 1)
- Model strategy in `sim/models/`: use a TI REF200 SPICE model if one exists; else ideal
  current source(s) ∥ finite output resistance (~50 MΩ) + a calibrated current-noise source
  (1 nA p-p 0.1–10 Hz; 20 pA/√Hz @10 kHz). RTD = swept resistor; R_ref = parameter.
- Decks in `sim/netlists/` for: (1) DC op / compliance margin, (2) ratiometric sanity
  `R_calc=R_ref·V_RTD/V_ref`, (3) Monte-Carlo accuracy → **equivalent °C error**,
  (4) compliance corner, (5) transient RC settling vs mux dwell, (6) `.noise` vs T7 ADC
  floor, (7) optional shared-ground crosstalk.
- `sim/scripts/`: ngspice batch runners (`ngspice -b deck.cir -o ...`) + python analysis/
  plots.
- One markdown report per test in `reports/sim/` using the `TESTING_PLAN.md` skeleton, each
  with explicit pass/fail vs its acceptance criterion.

## Done when
- All decks run headless and reproducibly via a single `sim/scripts/run_all` entry point.
- The accuracy budget yields a concrete °C number dominated by R_ref (sanity: 0.01 %/10 ppm
  over ~10 °C should land well under ±0.1 °C — confirm).
- Noise test confirms excitation + passive chain sits below the T7 ADC floor.
- Committed on branch `trackB`; track log updated.

## Coordination
Branch `trackB`, own worktree. Commit; do not merge. Note in your log that at **Wave 3**
the decks must be re-pointed from the modeled netlist to the KiCad-exported netlist
(`sim/netlists/ref200-rtd.net`) — leave a clear hook for that swap. Log to
`docs/sessions/trackB.md`.
