# TRACK F — Layout  *(Wave 2 — gated)*

> **Do not start until:** Track E (schematic, ERC-clean) and Track A (footprints) are merged
> into `integration`. Single session — layout does not parallelize on one board.

Claude Code session, **Track F**. Read `CLAUDE.md`, `docs/board_spec.md` (§Layout-critical,
§Interfaces), `docs/BOARD_DEV_CHECKLIST.md` (Phases 2–3), `docs/SESSION_KICKOFF.md`, and your
log `docs/sessions/trackF.md`. Work **only** in your owned paths.

## Owned paths (exclusive write)
`hardware/*.kicad_pcb`, `hardware/rtd-readout.kicad_pro` (board-setup/netclass settings)

## Must NOT touch
`hardware/*.kicad_sch` (frozen from E — request a schematic change via integration if
needed), `libraries/`, `sim/`, `host/`, `test/`, `scripts/`.

## Goal
Lay out and route the board, DRC-clean against the target fab rules, protecting the
precision-analog path.

## Layout priorities (in order)
1. **Board setup first:** track/space, drill, annular ring to the chosen fab; netclasses
   `SENSE` (V_RTD + V_ref pairs), `POWER`, `I2C`, default — set before routing.
2. **Star ground:** RTD force-returns + analog ground to one point; no long shared return
   between channels.
3. **RTD at the bottom of each loop**; full 4-wire Kelvin to the RTD connectors.
4. **Mixed-signal partition (critical):** separate analog and digital ground regions with a
   single-point tie; keep SDA/SCL and the ADS1115 digital side **away from** R_ref taps and
   sense pairs.
5. **Each ADS1115 next to its two R_ref pairs;** V_ref input pairs short and tight.
6. **Sense-line RC filter** (≈1 kΩ + 0.1 µF differential) at the T7 output, sized to settle
   within the mux dwell.
7. Connectors labeled (RTD channels, T7 analog pairs, I²C); test points on silk; ADS1115
   addresses on silk; mounting holes; fiducials if assembled; rev marking.

## Done when
- DRC clean: **0 violations**; zones refilled.
- 3D render + schematic-PCB consistency reviewed; every net reviewed (no blind autoroute),
  especially sense/V_ref separation, star ground, analog/digital partition.
- Tag `rev-A` before any fab drop (fab is Track G).
- Committed on `trackF`; log updated.

## Coordination
Branch `trackF` off post-E `integration`. Commit; integration merges F before G. Log to
`docs/sessions/trackF.md`.
