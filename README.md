# RTD Readout Board

Multi-channel 4-wire RTD readout for a LabJack T7 Pro.

Each RTD gets its own constant-current loop: a **current-regulator diode (CRD, ~220 µA)**
drives a precision **reference resistor R_ref** in series with the RTD. The RTD voltage
**V_RTD** is read on the T7's existing differential pairs; the current-sense voltage
**V_ref** is digitized on-board by **I²C ADS1115** ADCs on the T7's digital lines. Each RTD
is then computed **ratiometrically** as `R_RTD = C · (V_RTD / V_ref)`, where the per-channel
constant `C` is found by one-time **cross-calibration** against a known resistor. This makes
the result independent of the CRD's accuracy and R_ref's absolute value, and fits within the
T7's already-committed 7 analog pairs by moving V_ref onto the I²C bus.

## Where to start
- **Design:** `docs/board_spec.md` (electrical source of truth).
- **Working with Claude Code:** `CLAUDE.md` → `docs/SESSION_KICKOFF.md`.
- **Running multiple sessions in parallel:** `docs/PARALLEL_PLAN.md` + `docs/tasks/`.
- **Process:** `docs/DIRECTORY_MANAGEMENT.md`, `docs/BOARD_DEV_CHECKLIST.md`,
  `docs/TESTING_PLAN.md`.

## Toolchain
KiCad <pin version>, ngspice, python (+ LabJack LJM for `host/`). Validation gates:
`scripts/run_gates` (Track D). 

> This README is expanded by **Track D** (architecture summary, exact gate/fab commands,
> pinned versions).
