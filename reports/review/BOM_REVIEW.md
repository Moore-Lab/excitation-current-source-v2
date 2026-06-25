# BOM Review — rev-A (3-channel RTD readout)

Source: `fab/bom/bom_fab.csv` (exported from `hardware/rtd-readout.kicad_sch` at rev-A).
Cross-checked against `docs/board_spec.md` derived counts for a **Pt100, 3-channel** board.

| Refdes | Qty | Part | Spec rule | Check |
|--------|-----|------|-----------|-------|
| D1–D3 | 3 | CRD ~220 µA (CDLL5283) | CRD = channels = 3 | ✅ |
| R1–R3 | 3 | 910 Ω ≤10 ppm/°C thin-film (R_ref) | R_ref = channels = 3 | ✅ |
| R4,R5 | 2 | 4.7 kΩ I²C pull-ups | one SDA + one SCL pull-up | ✅ |
| U1,U2 | 2 | ADS1115IDGS (0x48 / 0x49) | ADS1115 = ceil(3/2) = 2 | ✅ |
| C1,C2 | 2 | 0.1 µF per-chip decoupling | one per ADS1115 | ✅ |
| C3,C4 | 2 | 10 µF bulk (+5V / VS) | bulk on each rail | ✅ |
| J1–J3 | 3 | 4-wire RTD screw terminals | RTD conns = channels = 3 | ✅ |
| J4 | 1 | Conn_T7_Analog (2×4 header) | 3 Sense± pairs + AGND out | ✅ |
| J5 | 1 | Conn_T7_I2C (1×4 header) | SDA/SCL/VS/GND out | ✅ |
| J6 | 1 | Conn_Power (2-pos screw) | +VIN / GND in | ✅ |
| TP1–TP10 | 10 | TestPoint pads | TOP/MID/rail/GND/SDA/SCL taps | ✅ |

**Total: 30 components / 12 BOM line items. All board_spec count rules pass.**

Open metadata note: generic passives (C1–C4, R4/R5, J4/J5) carry placeholder MPN fields
("set per value at BOM time" / "generic"). Precision parts (CRD, R_ref, ADS1115, RTD/power
terminals) are fully fielded with real MPNs. Assign generic-passive MPNs at order time.
