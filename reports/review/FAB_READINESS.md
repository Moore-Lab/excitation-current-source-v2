# Fab-Readiness Check — rev-A

Board: `hardware/rtd-readout.kicad_pcb` (frozen at tag `rev-A`). Package: `fab/` (tag `fab-rev-A`).

## Stackup
- **4 copper layers**, signal: `F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu`.
- Board thickness **1.6 mm**; dielectric layers present in the KiCad stackup.
- Board outline defined on `Edge.Cuts` (exported as `rtd-readout-Edge_Cuts.gm1`).

## Design rules (manufacturable by standard 4-layer fabs)
| Netclass | Track | Via (Ø/drill) | Clearance |
|----------|-------|---------------|-----------|
| Default | 0.25 mm | 0.6 / 0.3 mm | 0.13 mm |
| I2C | 0.25 mm | 0.6 / 0.3 mm | 0.13 mm |
| SENSE | 0.25 mm | 0.6 / 0.3 mm | 0.13 mm |
| POWER | 0.50 mm | 0.8 / 0.4 mm | 0.13 mm |

Board minimums: min track 0.13 mm, min hole 0.2 mm. All within common fab capability
(≈0.1 mm track/space, 0.2 mm drill).

## Gerber/drill package (`fab/`)
- Gerbers: F/B Cu, In1/In2 Cu, F/B Mask, F/B Silkscreen, F/B Paste, F/B Adhesive,
  F/B Courtyard, F/B Fab, Edge_Cuts, Margin, User_* + `.gbrjob`.
- Drill: `rtd-readout.drl`.
- Placement: `pos/rtd-readout-pos.csv` (mm).
- 3D: `rtd-readout.step`.
- BOM: `bom/bom_fab.csv`.

## Gates at this rev
- ERC **0 errors / 0 warnings** (`reports/erc/erc_rev-A.json`).
- DRC **0 violations / 0 unconnected** (`reports/drc/drc_rev-A.json`).
- Schematic parity: 47 non-blocking issues — mechanical footprints without symbols
  (mounting holes / fiducials) + un-synced footprint metadata fields. No net/connectivity
  errors. (Pre-existing in Track F; documented in SESSION_LOG Session 004.)

## Not done here (out of scope / needs hardware)
- **Panelization** — single-board outline only; add at the fab portal if required.
- **Bench verification** (TESTING_PLAN Part 2: cross-cal, noise/position-independence,
  thermal C-drift, CRD-noise) — requires the physical board; Lucas runs on assembly.
