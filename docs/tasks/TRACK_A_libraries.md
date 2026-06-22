# TRACK A — Component Libraries

Claude Code session, **Track A**, parallel. Read `CLAUDE.md`, `docs/board_spec.md`
(§Components, §Interfaces), `docs/DIRECTORY_MANAGEMENT.md` (library section), and your log
`docs/sessions/trackA.md` (create if absent). Work **only** in your owned paths.

## Owned paths (exclusive write)
`libraries/**`, `hardware/sym-lib-table`, `hardware/fp-lib-table`

## Must NOT touch
Any `.kicad_sch/.kicad_pcb`, `sim/`, `host/`, `test/`, `scripts/`; shared docs read-only.

## Goal
Project-local symbol + footprint + 3D libraries so the schematic (Track E) builds
reproducibly, independent of global KiCad libs.

## Parts to create & verify
- **CRD** — 1N5283 / **CDLL5283** (MELF for SMD). Two-terminal, polarized (anode/cathode).
  Verify footprint land pattern + polarity marking against datasheet.
- **Reference resistor R_ref** — symbol carries **Tempco (≤10 ppm/°C)** and stability fields;
  note in the symbol that absolute tolerance is not the spec (cross-cal absorbs value).
- **ADS1115** — correct package (e.g. VSSOP-10); pin map verified vs datasheet
  (AINx, ADDR, ALERT/RDY, SCL, SDA, VDD, GND). Symbol should make the ADDR strap obvious.
- **Connectors:** RTD 4-wire input; T7 analog (CB37) sense-pair output; T7 digital
  (SDA/SCL/VS/GND) output. Screw terminals/headers per the interface list.
- I²C pull-up resistors, decoupling caps, test points.
- Datasheets → `docs/datasheets/`.

## Done when
- `sym-lib-table`/`fp-lib-table` point **only** at `libraries/`.
- Every symbol fully fielded (value, footprint, MPN, manufacturer, datasheet; R_ref also
  tempco).
- Footprints rendered and pad geometry + pin mapping checked vs datasheets — **call out the
  CRD polarity and ADS1115 pinout explicitly in your log** (silent-fatal items).
- Committed on `trackA`; log updated with verification evidence.

## Coordination
Branch `trackA`, own worktree. Commit; **do not merge** — integration pulls A first
(libraries gate the schematic). Log to `docs/sessions/trackA.md`.
