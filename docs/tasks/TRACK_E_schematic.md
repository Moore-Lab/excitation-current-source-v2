# TRACK E — Schematic Capture  *(Wave 1 — gated)*

> **Do not start until:** Track A is merged into `integration` (symbols/footprints exist)
> **and** Lucas has resolved RTD type + channel count (`board_spec.md` open inputs). Branch
> off the post-A `integration`.

Claude Code session, **Track E**. Read `CLAUDE.md`, `docs/board_spec.md` (all),
`docs/BOARD_DEV_CHECKLIST.md` (Phase 1), `docs/SESSION_KICKOFF.md`, and your log
`docs/sessions/trackE.md`. Work **only** in your owned paths.

## Owned paths (exclusive write)
`hardware/*.kicad_sch`, `hardware/rtd-readout.kicad_pro` (schematic-side settings)

## Must NOT touch
`hardware/*.kicad_pcb` (Track F), `libraries/` (Track A), `sim/`, `host/`, `test/`,
`scripts/`.

## Goal
Capture the full schematic from `board_spec.md`, ERC-clean, using only project-local
library parts.

## Build (hierarchical sheets)
- **`unit_cell` sheet (×N channels):** CRD (anode→rail, cathode→R_ref) → R_ref → RTD 4-wire
  connector; RTD at the bottom of the loop to GND; Force/Sense as separate nets; Kelvin at
  the RTD. Tap V_ref differentially at the R_ref pads.
- **`ads1115` sheet:** 1 chip per 2 channels; each chip's two differential inputs wired to
  two channels' R_ref taps; **unique ADDR straps (0x48–0x4B)**; per-chip decoupling; one set
  of SDA/SCL pull-ups; supply from T7 VS or a regulated 3.3–5 V.
- **`power` + `connectors` sheets:** rail/LDO + decoupling; RTD connectors; the 7 Sense±
  pairs out to the T7 analog (CB37); SDA/SCL/VS/GND out to the T7 digital. Only V_RTD leaves
  as analog.
- Test points on each TOP node, each Sense+/MID node, rail, GND, SDA, SCL.
- Every symbol fully fielded; power flags; meaningful per-channel net labels.

## Done when
- ERC clean: **0 errors** (warnings fixed or justified in the log).
- BOM exported and cross-checked vs `board_spec.md` (CRD = channels, ADS1115 = ceil(ch/2),
  R_ref = channels, pull-ups/decoupling present).
- Netlist exported to `sim/netlists/rtd-readout.net` for Track B's Wave-3 re-point.
- Committed on `trackE`; log updated.

## Coordination
Branch `trackE` off post-A `integration`. If split: **E1** owns `unit_cell`, **E2** owns
`ads1115`+`power`+`connectors`; one owns the root sheet — coordinate the hand-off. Commit;
integration merges E before F. Log to `docs/sessions/trackE.md`.
