# TRACK C — Acquisition (host/) & Bench Procedures

Claude Code session, **Track C**, parallel. Read `CLAUDE.md`, `docs/board_spec.md`
(§The measurement, §Components, §Interfaces), `docs/TESTING_PLAN.md` (Part 2 + report
format), and your log `docs/sessions/trackC.md` (create if absent). Work **only** in your
owned paths.

## Owned paths (exclusive write)
`host/**`, `test/**`

## Must NOT touch
`hardware/`, `libraries/`, `sim/`, `scripts/`; shared docs read-only.

## Goal
Write the reusable acquisition library (`host/`) and the staged bench procedures (`test/`)
so the moment the board exists, Lucas runs the tests with no glue work. No hardware needed
to write/lint this; dry-run against mock data.

## `host/` — the acquisition library (this is the real measurement code, not scaffolding)
- **T7 driver (LJM):** read each RTD's V_RTD on its existing differential pair; correct range
  (Pt100 ±0.1 V, Pt1000 ±1 V); configurable settling / resolution index (guard the mux-
  settling risk).
- **ADS1115 driver (I²C over the T7's digital lines via LJM):** configure PGA range
  (default ±0.256 V), address each of up to 4 chips (0x48–0x4B), read V_ref **differentially**
  per channel, average N conversions to beat LSB noise.
- **Time-aligned dual read:** sample T7 V_RTD and ADS1115 V_ref close in time per channel
  (CRD current is steady, so modest skew is fine — but structure the read for it).
- **Ratiometric + cross-cal math:** store a per-channel constant `C`; compute
  `R_RTD = C·(V_RTD/V_ref)`. Provide a calibration routine that, given a known resistor,
  computes `C = R_known·(V_ref/V_RTD)`. Persist C per channel.

## `test/` — staged procedures (import `host/`), per TESTING_PLAN Part 2
- Stage 1 power & **I²C bring-up / address scan** (detect all ADS1115).
- Stage 2 **cross-calibration** (substitute known 0.01 % resistor; compute & store C).
- Stage 3 ratiometric accuracy (decade box / known resistors).
- Stage 5 **noise + position-independence** — include tooling to load the old series-chain
  data and compare directly (the headline acceptance test).
- Stage 7 thermal soak watching **C drift** (validates R_ref + relative-gain-tempco term).
- Stage 8 CRD-noise check.
- Data schema + logging into `test/data/` (committed); reports to `reports/test/`.

## Done when
- `host/` and `test/` import/lint clean; dry-run against synthetic T7/ADS1115 data with no
  hardware; parameterized for Pt100/Pt1000 and up to 7 channels.
- Committed on `trackC`; log updated.

## Coordination
Branch `trackC`, own worktree. Commit; do not merge. Independent of other Wave-0 tracks.
Log to `docs/sessions/trackC.md`.
