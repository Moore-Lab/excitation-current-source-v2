# Datasheets — REF200 RTD board

Index of part datasheets and the **verified parameters** the Track-A libraries were built
from. Where a PDF is committed here it is the authoritative copy; where only a URL is given,
the vendor blocks automated download (TI/Vishay/Mouser anti-bot) or the file is large — grab
it manually if you need the full document. Parameters below are what the symbol/footprint
fields encode, so the schematic (Track E) can be reviewed without opening each PDF.

| Part | Role | Datasheet | Local PDF |
|------|------|-----------|-----------|
| REF200AU | Dual 100 µA current source (excitation) | https://www.ti.com/lit/ds/symlink/ref200.pdf | — (TI interstitial blocks curl) |
| Vishay VSMP1206 (100 Ω) | Precision reference resistor R_ref | https://www.vishaypg.com/docs/63001/vsmp.pdf | — (vendor anti-bot) |
| TI LP2985-5.0 | Low-noise 5.0 V LDO | https://www.ti.com/lit/ds/symlink/lp2985.pdf | — (10 MB; URL only) |
| 1N4148W | Optional reverse-V protection diode | https://www.diodes.com/assets/Datasheets/ds30086.pdf | `1N4148W_diodes.pdf` ✓ |
| Phoenix MKDS 1,5/x-5,08 | Screw terminals (RTD 4-wire, power) | https://www.phoenixcontact.com (search "MKDS 1,5/4-5,08") | — |

## Verified parameters (encoded in the library fields)

### REF200AU — Texas Instruments — SOIC-8 (Package_SO: SOIC-8_3.9x4.9mm_P1.27mm, JEDEC MS-012AA)
Pin map (from `board_spec.md` §2, cross-checked against KiCad's official `Reference_Current:REF200AU`):

| Pin | Name | Pin | Name |
|----:|------|----:|------|
| 1 | I1 Low (source 1 out) | 5 | Mirror Input (unused) |
| 2 | I2 Low (source 2 out) | 6 | Substrate → GND |
| 3 | Mirror Common (unused) | 7 | I2 High (source 2 supply) |
| 4 | Mirror Output (unused) | 8 | I1 High (source 1 supply) |

Used in **Mode B** (independent sources, 100 µA each): pin 8→+5 V, pin 1→R_ref_A→RTD_A;
pin 7→+5 V, pin 2→R_ref_B→RTD_B. Substrate (6) to GND. Mirror (3/4/5) left open (NC).

### Vishay VSMP1206 — 100 Ω reference resistor — R_1206_3216Metric
- **Selected MPN:** `Y1625100R000Q9R` (in-stock at RS/Mouser): 100 Ω, **±0.02 %**, **±0.2 ppm/°C**, 0.33 W, Z-Foil.
- Spec target is 0.01 % / ≤10 ppm/°C. Tempco (0.2 ppm/°C) beats the requirement ~50×.
  The ±0.01 % tolerance grade of the **same VSMP1206 series is a drop-in** (identical 1206
  footprint) if untrimmed absolute tolerance matters; in this **ratiometric** design R_ref is
  measured per board, so tempco/drift — not initial tolerance — dominates. See trackA log.

### TI LP2985-5.0 — low-noise LDO — SOT-23-5
- MPN `LP2985IM5X-5.0/NOPB`. 150 mA, fixed 5.0 V, low-noise (BYP pin). Pinout (SOT-23-5):
  1 VIN, 2 GND, 3 EN (ON/OFF), 4 BYP, 5 VOUT. Board draws ~0.5 mA (4×100 µA + housekeeping),
  far inside 150 mA. The 3.3 V grade (LP2985-3.3) is a drop-in if a 3.3 V rail is preferred.
- **The LDO is the least-critical part** (spec §4: ratiometric rejects rail noise). Treat the
  exact LDO as a power-stage design choice; LT3045/ADP7142 are lower-noise alternatives but
  need their own footprint/pinout.

### 1N4148W — Diodes Inc — SOD-123
- MPN `1N4148W-7-F`. Optional, one per source, anti-parallel for reverse-V clamp (REF200
  datasheet Fig. 17a). Footprint pad 1 = cathode (matches symbol pin 1 = K).

### Phoenix Contact MKDS 1,5/x-5,08 — screw terminals
- `MKDS 1,5/4-5,08` (1×04, RTD: Force+/Sense+/Sense−/Force−) and `MKDS 1,5/2-5,08`
  (1×02, +5 V_IN/GND). 5.08 mm pitch, THT, horizontal wire entry.
