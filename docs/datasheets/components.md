# Datasheet index & verified specs — Track A component libraries

Provenance for every part in `libraries/`. Each library symbol carries a `Datasheet`
field with the canonical URL; this file records the verification evidence behind the
footprint + pinout choices. Local PDFs are committed here where licensing/availability
allows; otherwise the canonical link is given.

| Part | Symbol | Footprint | Datasheet |
|------|--------|-----------|-----------|
| CRD **LIS J500 TO-92 2L** (rev-E) | `CRD_1N5283` (legacy name) | `TO-92-2_CRD-J500` (TO-92 2-lead THT) | [LIS J500 series](https://www.linearsystems.com/currentregulatingdiodes/j500-series) |
| Reference resistor R_ref | `R_ref` | `R_1206_3216Metric` | [KOA RN73H](https://www.koaspeer.com/pdfs/RN73H.pdf) — RN73H2BTTD8200B10, 820 Ω, ±0.1 %, ±10 ppm/°C (rev-E) |
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

### CRD LIS J500 (TO-92 2L) — package & polarity (rev-E)
- **Package:** TO-92, 2 leads at the outer 0.100 in positions (2.41–2.67 mm per LIS doc
  201126 Rev A10 p.2). Footprint **`TO-92-2_CRD-J500`** — project-local copy of KiCad's
  `TO-92-2` with the **body/silk mirrored about the pad axis** and the drill opened to
  **0.8 mm** (worst-case J500 lead diagonal is 0.755 mm; pads 1.35 × 1.6 mm). Replaces the
  rev-A–D CDLL5283 DO-213AB MELF (unbuyable + hand-assembly-hostile).
- **Polarity (silent-fatal):** the schematic keeps **pin 1 = K, pin 2 = A** (`CRD_1N5283`
  symbol, legacy name). The J500's physical pinout *facing the flat/marked face* is
  **pin 1 = A (left), pin 2 = K (right)** — the mirrored footprint absorbs the difference:
  **insert the part with its flat face matching the silk outline and the cathode lands in
  pad 1** (marked "K" on the silk, west side). Verify on arrival with a bench supply: a CRD
  conducts a constant ~0.24 mA in the A→K direction above ~1.2 V.
- **Schematic intent (board_spec §Current source):** anode → +V rail, cathode → R_ref
  → **pad 2 (A)** to the rail, **pad 1 (K)** to the R_ref/TOP node (unchanged from rev-D).

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
- **R_ref MPN is pinned (rev-E): KOA RN73H2BTTD8200B10** (820 Ω, ±0.1 %, ±10 ppm/°C, 1206).
  Value and tolerance are absorbed by the cross-cal constant; the *binding* spec is tempco
  ≤10 ppm/°C + long-term stability (board_spec §R_ref). Any ≤10 ppm/°C 715–820 Ω thin-film/
  foil part is an acceptable substitute (keep ≤820 Ω so the J500 band max never clips).
- **3D models** for the copied footprints resolve via the standard `${KICAD10_3DMODEL_DIR}`
  env var (render-only; does not affect netlist/ERC/DRC/fab). Project-local STEP files were
  intentionally not vendored.
