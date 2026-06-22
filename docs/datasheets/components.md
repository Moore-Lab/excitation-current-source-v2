# Datasheet index & verified specs — Track A component libraries

Provenance for every part in `libraries/`. Each library symbol carries a `Datasheet`
field with the canonical URL; this file records the verification evidence behind the
footprint + pinout choices. Local PDFs are committed here where licensing/availability
allows; otherwise the canonical link is given.

| Part | Symbol | Footprint | Datasheet |
|------|--------|-----------|-----------|
| CRD 1N5283 / **CDLL5283** | `CRD_1N5283` | `D_MELF` (DO-213AB) | [Microchip CDLL5283](https://www.microchip.com/en-us/product/cdll5283-current-regulator-diode) |
| Reference resistor R_ref | `R_ref` | `R_1206_3216Metric` | [Susumu RG series](https://www.susumu.co.jp/common/pdf/n_catalog_partition06_en.pdf) (representative ≤10 ppm/°C thin-film) |
| Current-sense ADC | `ADS1115` | `MSOP-10_3x3mm_P0.5mm` (VSSOP-10 / DGS) | `ADS1115_ti_sbas444.pdf` (local) · [TI SBAS444](https://www.ti.com/lit/ds/symlink/ads1115.pdf) |
| RTD 4-wire input | `Conn_RTD_4W` | `TerminalBlock_Phoenix_MKDS-1,5-4-5.08_1x04_P5.08mm_Horizontal` | [Phoenix MKDS 1,5/4-5,08](http://www.farnell.com/datasheets/100425.pdf) |
| Power input | `Conn_Power` | `TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal` | [Phoenix MKDS 1,5/2-5,08](http://www.farnell.com/datasheets/100425.pdf) |
| T7 analog (CB37) out | `Conn_T7_Analog` | `PinHeader_2x04_P2.54mm_Vertical` | generic 2.54 mm header |
| T7 digital / I²C out | `Conn_T7_I2C` | `PinHeader_1x04_P2.54mm_Vertical` | generic 2.54 mm header |
| I²C pull-ups / general R | `R` | `R_0805_2012Metric` | generic |
| Decoupling / bypass C | `C` | `C_0603_1608Metric` | generic |
| Test point | `TestPoint` | `TestPoint_Pad_D1.5mm` | copper pad |

All footprints were copied from the KiCad 10.0.3 standard libraries (IPC-vetted) into the
project-local `rtd-readout.pretty`, then verified against the datasheet land pattern below.

## Silent-fatal verifications (the two parts that quietly break the board if wrong)

### CRD CDLL5283 — package & polarity
- **Package:** DO-213AB **MELF** (confirmed: Microchip/ex-Central Semiconductor CDLL5283/TR).
  DO-213AB MELF → KiCad **`D_MELF`** footprint (body fab ≈ 5.2 × 2.6 mm, pads at ±2.4 mm).
  (The smaller MELF, DO-213AA/MiniMELF, is `D_MiniMELF` — **not** this part.)
- **Polarity (silent-fatal):** KiCad universal diode convention is used and matches the
  footprint: **pad 1 = cathode (K)** — the banded end of the MELF — and **pad 2 = anode (A)**.
  `D_MELF` marks the cathode with the silk band/notch on the **pad-1 side**; its `F.Fab`
  diode glyph points to the same side. The `CRD_1N5283` symbol is drawn with **pin 1 = K,
  pin 2 = A**, so pin↔pad mapping is correct.
- **Schematic intent (board_spec §Current source):** anode → +V rail, cathode → R_ref.
  → in the schematic, **pin 2 (A)** goes to the rail and **pin 1 (K)** to the R_ref/TOP node.

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
- **R_ref MPN is representative.** Value (≈910 Ω) and tolerance are absorbed by the
  cross-cal constant; the *binding* spec is tempco ≤10 ppm/°C + long-term stability
  (board_spec §R_ref). Any ≤10 ppm/°C ~910 Ω thin-film/foil part is acceptable — confirm
  the exact orderable MPN at procurement.
- **3D models** for the copied footprints resolve via the standard `${KICAD10_3DMODEL_DIR}`
  env var (render-only; does not affect netlist/ERC/DRC/fab). Project-local STEP files were
  intentionally not vendored.
