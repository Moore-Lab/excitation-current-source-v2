# TRACK A — Component Libraries

You are a Claude Code session working **Track A** in parallel with others. Read
`CLAUDE.md`, `docs/board_spec.md` (esp. §2 pinout, §3 values, §7 BOM),
`docs/DIRECTORY_MANAGEMENT.md` (library section), and your track log
`docs/sessions/trackA.md` (create it if absent). Then work **only** within your owned
paths.

## Owned paths (exclusive write)
`libraries/**`, `hardware/sym-lib-table`, `hardware/fp-lib-table`

## Must NOT touch
Any `.kicad_sch` / `.kicad_pcb`, `sim/`, `test/`, `scripts/`, shared docs (read-only).

## Goal
Stand up project-local symbol + footprint + 3D libraries so the schematic (Track E) can be
built reproducibly, independent of global KiCad libraries.

## Deliverables
- Project-local libraries under `libraries/symbols`, `libraries/footprints/*.pretty`,
  `libraries/3dmodels`, with `sym-lib-table`/`fp-lib-table` pointing **only** at them.
- Verified parts:
  - **REF200** (SOIC-8): symbol pin mapping **must match** the datasheet table in
    `board_spec.md` §2 (1 I1Low, 2 I2Low, 3 MirrorCom, 4 MirrorOut, 5 MirrorIn,
    6 Substrate, 7 I2High, 8 I1High). Footprint = standard SOIC-8; verify land pattern
    against the datasheet.
  - **Precision reference resistor** — carry fields for 0.01 %, ≤10 ppm/°C and a real MPN.
    This is the accuracy-limiting part; do not use a generic resistor symbol.
  - LDO, screw-terminal connector, 1N4148 (optional protection), test points.
- Each symbol fully fielded: value, footprint, MPN, manufacturer, datasheet.
- Datasheets saved to `docs/datasheets/`.

## Done when
- `kicad-cli fp` / `kicad-cli sym` operations succeed on the libraries; footprints rendered
  to SVG (`reports/` is off-limits, render to `libraries/_verify/` and delete before
  commit, or just inspect) and pad geometry sanity-checked against datasheets.
- Pin-to-pad mapping for REF200 and the connector double-checked (a wrong pinout here is
  silent and fatal — call it out explicitly in your log).
- Committed on branch `trackA`; track log updated with the verification evidence.

## Coordination
You are on branch `trackA` in your own worktree. Commit there. **Do not merge** — the
integration step pulls you in first (libraries gate the schematic). Log to
`docs/sessions/trackA.md`, not the global log.
