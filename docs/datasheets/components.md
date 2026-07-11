# Datasheet index & verified specs — Track A component libraries

Provenance for every part in `libraries/`. Each library symbol carries a `Datasheet`
field with the canonical URL; this file records the verification evidence behind the
footprint + pinout choices. Local PDFs are committed here where licensing/availability
allows; otherwise the canonical link is given.

| Part | Symbol | Footprint | Datasheet |
|------|--------|-----------|-----------|
| CRD **SEMITEC S-101T** (rev-F) | `CRD_1N5283` (legacy name) | `D_SEMITEC_S-101T` (SMD flat 2-lead, custom from catalog land pattern) | [SEMITEC CRD catalog](https://www.semitec-global.com/uploads/2022/01/P22-23-CRD.pdf) |
| Reference resistor R_ref | `R_ref` | `R_1206_3216Metric` | [Vishay TNPU e3](https://www.vishay.com/docs/28779/tnpue3.pdf) — TNPU12061K00AWEN00, 1.00 kΩ, ±0.05 %, ±2 ppm/°C (rev-F) |
| Current-sense ADC | `ADS1115` | `MSOP-10_3x3mm_P0.5mm` (VSSOP-10 / DGS) | `ADS1115_ti_sbas444.pdf` (local) · [TI SBAS444](https://www.ti.com/lit/ds/symlink/ads1115.pdf) |
| RTD 4-wire input | `Conn_RTD_4W` | `TerminalBlock_Phoenix_MKDS-1,5-4-5.08_1x04_P5.08mm_Horizontal` | [Phoenix MKDS 1,5/4-5,08](http://www.farnell.com/datasheets/100425.pdf) |
| Power input | `Conn_Power` | `TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal` | [Phoenix MKDS 1,5/2-5,08](http://www.farnell.com/datasheets/100425.pdf) |
| T7 analog (CB37) out | `Conn_T7_Analog` | `PinHeader_2x04_P2.54mm_Vertical` | generic 2.54 mm header |
| T7 digital / I²C out | `Conn_T7_I2C` | `PinHeader_1x04_P2.54mm_Vertical` | generic 2.54 mm header |
| I²C pull-ups / general R | `R` | `R_0805_2012Metric` | generic |
| Decoupling / bypass C | `C` | `C_0805_2012Metric` (rev-E; was 0603) | generic |
| Test point | `TestPoint` | `TestPoint_Pad_D1.5mm` | copper pad |

All footprints were copied from the KiCad 10.0.3 standard libraries (IPC-vetted) into the
project-local `rtd-readout.pretty`, then verified against the datasheet land pattern below.

## Silent-fatal verifications (the two parts that quietly break the board if wrong)

### CRD SEMITEC S-101T — package & polarity (rev-F)
- **Package:** SMD flat 2-lead resin package, body 2.6 × 1.6 × 0.7 mm, 3.5 mm tip-to-tip.
  Footprint **`D_SEMITEC_S-101T`** — custom, from SEMITEC's own recommended land pattern
  (catalog p.23, S series): pads 1.2 × 1.6 mm at **3.4 mm centers** (2.2 mm gap). All
  catalog dimensions are nominals (no tolerances published). Replaces the rev-E J500 TO-92
  (current lowered ~2.4× for cryostat self-heating).
- **Polarity (silent-fatal):** the schematic keeps **pin 1 = K, pin 2 = A** (`CRD_1N5283`
  symbol, legacy name). The S-101T marks the **cathode with a hatched band across one end
  of the marked (top) face** — place that band toward **pad 1** (the heavy silk bar + "K"
  marker side). In tape, the cathode faces the sprocket-hole side. Verify on arrival with a
  bench supply: a CRD conducts a constant ~0.10 mA in the A→K direction above ~1–2 V.
- **Schematic intent (board_spec §Current source):** anode → +V rail, cathode → R_ref
  → **pad 2 (A)** to the rail, **pad 1 (K)** to the R_ref/TOP node (unchanged since rev-A).

### ADS1115IDGS — VSSOP-10 pinout
- **Package:** TI **DGS = VSSOP-10**, JEDEC MO-187 variation BA, 3 × 3 mm body, **0.5 mm
  pitch**. KiCad's `MSOP-10_3x3mm_P0.5mm` is exactly MO-187 var BA → correct land pattern.
- **Pinout (silent-fatal), verified three ways (TI datasheet text mirror, KiCad
  `Analog_ADC` symbol, and known good breakouts — all agree):**

  | Pin | Name | Pin | Name |
  |-----|------|-----|------|
  | 1 | ADDR | 6 | AIN2 |
  | 2 | ALERT/RDY | 7 | AIN3 |
  | 3 | GND | 8 | VDD |
  | 4 | AIN0 | 9 | SDA |
  | 5 | AIN1 | 10 | SCL |

- **ADDR strap → I²C address:** GND = 0x48, VDD = 0x49, SDA = 0x4A, SCL = 0x4B.
  This board (3 ch → 2 chips, board_spec Resolved inputs #2): **0x48 (ADDR→GND)** and
  **0x49 (ADDR→VDD)**. Documented in the symbol's `I2C_Address` field.

## Notes
- **R_ref MPN is pinned (rev-F): Vishay TNPU12061K00AWEN00** (1.00 kΩ, ±0.05 %, ±2 ppm/°C,
  1206 bulk-thin-film). Value and tolerance are absorbed by the cross-cal constant; the
  *binding* spec is tempco + long-term stability (board_spec §R_ref). Any ≤10 ppm/°C
  ~1.00 kΩ thin-film/foil part is an acceptable substitute (keep ≤1.1 kΩ so the S-101T
  band max 0.21 mA never clips the ±0.256 V range).
- **Sense-path passives (rev-F policy):** C5–C8 = **C0G/NP0** 0.1 µF 50 V 1206 (Murata
  GRM31C5C1H104JA01L — Class-1: no DC-bias/temperature capacitance drift, no piezo);
  R7–R14 = 0.1 %, ±25 ppm/°C thin film (Susumu RG2012P-102-B, order same-reel for
  matching). Rail decoupling (C1,C2) and bulk (C3,C4) stay X7R/X5R — not in the
  measurement path, and 10 µF does not exist in C0G.
- **3D models** for the copied footprints resolve via the standard `${KICAD10_3DMODEL_DIR}`
  env var (render-only; does not affect netlist/ERC/DRC/fab). Project-local STEP files were
  intentionally not vendored.
