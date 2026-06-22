# Track A — Component Libraries (session log)

Per-track log, newest entry on top. Schema mirrors `docs/SESSION_LOG.md`.

---

## Track A — 2026-06-22 — Stand up project-local symbol + footprint libraries

**Tooling:** KiCad **10.0.3** (release, build May 14 2026), ngspice 46. `kicad-cli` at
`C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`.
**Branch / commit at start:** `trackA` @ d54eb69 (worktree `../rtd-trackA`).
**State before:** `libraries/{symbols,footprints,3dmodels}` and `hardware/` held only
`.gitkeep`. No lib tables. board_spec Resolved inputs locked (Pt100, 3 ch → 2 ADS1115).

**Objective:** Project-local symbol + footprint libraries so the Track E schematic builds
reproducibly, independent of global KiCad libs; lib tables pointing only at `libraries/`.

**Actions:**
1. Verified the two silent-fatal parts against datasheets (see Validation below).
2. Built `libraries/footprints/rtd-readout.pretty` by copying 10 IPC-vetted footprints from
   the KiCad 10.0.3 standard libraries (so geometry is known-good and already in v10 format),
   each verified against the datasheet land pattern.
3. Authored `libraries/symbols/rtd-readout.kicad_sym` — 10 symbols, every one fully fielded
   (Value, Footprint, MPN, Manufacturer, Datasheet, Description; R_ref also Tempco +
   Stability; ADS1115 also I2C_Address + Package; CRD also Polarity). Normalized to canonical
   v10 format with `kicad-cli sym upgrade`.
4. Wrote `hardware/sym-lib-table` and `hardware/fp-lib-table`, each a single `rtd-readout`
   entry via `${KIPRJMOD}/../libraries/...` — **only** project-local, no global refs.
5. Added datasheet provenance: `docs/datasheets/components.md` (index + verified specs) and
   `docs/datasheets/ADS1115_ti_sbas444.pdf` (local copy).

**Files touched:**
- `libraries/symbols/rtd-readout.kicad_sym`
- `libraries/footprints/rtd-readout.pretty/*.kicad_mod` (10 footprints)
- `hardware/sym-lib-table`, `hardware/fp-lib-table`
- `docs/datasheets/components.md`, `docs/datasheets/ADS1115_ti_sbas444.pdf`

**Library contents (10 symbols / 10 footprints):**
| Symbol | Ref | Footprint | Notes |
|--------|-----|-----------|-------|
| `CRD_1N5283` | D | `D_MELF` | CRD, pin1=K / pin2=A |
| `R_ref` | R | `R_1206_3216Metric` | tempco ≤10 ppm/°C is the spec |
| `R` | R | `R_0805_2012Metric` | I²C pull-ups / general |
| `C` | C | `C_0603_1608Metric` | decoupling / bypass |
| `ADS1115` | U | `MSOP-10_3x3mm_P0.5mm` | VSSOP-10/DGS, ADDR strap fielded |
| `Conn_RTD_4W` | J | `…MKDS-1,5-4-5.08…1x04…` | Force+/Sense+/Sense−/Force− |
| `Conn_T7_Analog` | J | `PinHeader_2x04_P2.54mm_Vertical` | 3 Sense± pairs + 2 AGND |
| `Conn_T7_I2C` | J | `PinHeader_1x04_P2.54mm_Vertical` | VS/GND/SDA/SCL |
| `Conn_Power` | J | `…MKDS-1,5-2-5.08…1x02…` | +VIN/GND |
| `TestPoint` | TP | `TestPoint_Pad_D1.5mm` | probe pad |

**Validation (with numbers):**
- ERC / DRC / SPICE — n/a (no schematic/PCB yet; that's Track E).
- `kicad-cli sym upgrade --force` on the symbol lib → **exit 0** ("Saving … in updated format").
- `kicad-cli sym export svg` → **exit 0**, rendered **all 10/10 symbols** (parse check).
- `kicad-cli fp upgrade --force` on the .pretty → **exit 0** (footprints valid).
- `kicad-cli fp export svg` of `D_MELF` and `MSOP-10_3x3mm_P0.5mm` → exit 0 (visual check).
- All **10/10** symbol `Footprint` fields resolve to files present in `rtd-readout.pretty`.
- Both lib tables reference **only** `${KIPRJMOD}/../libraries/...` (zero global-lib refs).

**Silent-fatal items — called out explicitly (per brief):**
- **CRD polarity:** CDLL5283 is **DO-213AB MELF** → `D_MELF`. KiCad diode convention used:
  **pad 1 = cathode (banded end), pad 2 = anode**; `D_MELF` silk band/notch + F.Fab glyph
  are on the pad-1 side. Symbol drawn pin1=K / pin2=A, so symbol↔footprint polarity is
  consistent. Board net intent (board_spec): anode(pin2)→+V rail, cathode(pin1)→R_ref.
- **ADS1115 pinout:** VSSOP-10 (DGS, MO-187 var BA, 0.5 mm pitch) → `MSOP-10_3x3mm_P0.5mm`.
  Pinout verified 3 ways (TI datasheet mirror, KiCad `Analog_ADC` symbol, known breakouts;
  all agree): 1 ADDR · 2 ALERT/RDY · 3 GND · 4 AIN0 · 5 AIN1 · 6 AIN2 · 7 AIN3 · 8 VDD ·
  9 SDA · 10 SCL. ADDR strap→addr (GND/VDD/SDA/SCL = 0x48/49/4A/4B) fielded; this board uses
  0x48 + 0x49.

**Decisions (rationale + spec ref):**
- **Copied std KiCad footprints rather than hand-authoring pad geometry** — they are
  IPC-vetted and already in v10 format, eliminating land-pattern transcription error;
  verification reduces to confirming the std footprint matches the datasheet package.
- **R_ref = 1206, ~910 Ω** — 1206 for lower self-heating/better stability; 910 Ω puts V_ref
  ≈200 mV inside the ADS1115 ±0.256 V range (board_spec §R_ref). MPN is representative
  (≤10 ppm/°C); value/tolerance are cross-cal-absorbed.
- **R_ref footprint = `R_1206_3216Metric`** (reflow land), not the HandSolder variant.
- **One nickname each** (`rtd-readout`) for symbols and footprints — simplest table; mirrors
  the vendored reference project's structure.
- **3D models left on `${KICAD10_3DMODEL_DIR}`** — render-only, universally present with a
  KiCad 10 install; not vendored to keep the repo lean. Does not affect reproducibility of
  netlist/ERC/DRC/fab. `libraries/3dmodels/` kept as a placeholder.

**Open issues / risks:**
- **R_ref exact MPN** to be confirmed at procurement (any ≤10 ppm/°C ~910 Ω part is fine).
- **CDLL5283 PDF not vendored** — Microchip download URL returned an HTML stub; canonical
  product link is recorded in `docs/datasheets/components.md` and the symbol field.
- **`Conn_T7_Analog` / `Conn_T7_I2C` pin assignment** is a sensible default (2x04 / 1x04
  headers); Track E may re-pick the exact connector/pin count when it captures the schematic.
- 3D STEP for `D_MELF`/`MSOP-10` resolves only if the standard KiCad 3D shapes are installed
  (they are, with KiCad 10).

**Next action (integration):** Pull Track A **first** (libraries gate the schematic), then
start Track E off post-A `integration`. Track E binds these symbols/footprints into the
schematic and runs the first ERC.

**Commit:** 3f8c8f4 (libraries + lib tables + datasheets). Log hash filled in the follow-up.
