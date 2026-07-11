# BOARD_DEV_CHECKLIST.md

Gate list for good PCB development on this board. Nothing advances until the current phase's
checks pass. **Bold** items are specific to this design and are the ones most likely to
bite. Everything traces to `docs/board_spec.md`. Canonical gate commands are at the bottom.

---

## Phase 1 — Schematic capture

- [ ] Every symbol has value, footprint, MPN, manufacturer, datasheet. No blank fields.
- [ ] **CRD placed two-terminal in each loop** (anode→rail, cathode→R_ref), part =
      LIS J500 TO-92 (`board_spec.md` §Components; rev-E). Its tolerance is intentionally
      irrelevant — do not "improve" it with a precision source; the design measures current
      live.
- [ ] **R_ref annotated for stability, not tolerance:** ≤10 ppm/°C, low-noise, real MPN.
      **Absolute value is absorbed by cross-cal** — value is chosen to land V_ref in the
      ADS1115 range (default 820 Ω → ~197 mV; never clips at the +20 % CRD band max).
- [ ] **RTD at the bottom of each loop** (low common-mode) — the reason the board exists.
- [ ] **Force/Sense separate nets** to the RTD; Kelvin junction at the RTD, not on-board.
- [ ] **V_ref tapped differentially at the R_ref pads → ADS1115 IN±.** V_ref common-mode is
      a few hundred mV, inside the ADS1115 GND–VDD input range — confirm.
- [ ] **ADS1115 subsystem:** 1 chip per 2 channels; **ADDR straps give unique 0x48–0x4B**;
      per-chip decoupling; one set of SDA/SCL pull-ups (4.7 kΩ default); supply from T7 VS or
      regulated 3.3–5 V.
- [ ] **Interfaces present:** RTD 4-wire connectors; the 7 Sense± pairs out to the T7 analog
      (CB37); SDA/SCL/VS/GND out to the T7 digital. Only V_RTD leaves as analog — V_ref is
      digitized on-board.
- [ ] Power flags on rail/ground; meaningful per-channel net labels (`CH1_TOP`, `CH1_SENSE+`).
- [ ] **Test points** on each TOP node, each Sense+/MID node, rail, GND, SDA, SCL — add now
      so they net-connect.
- [ ] **ERC clean: 0 errors;** warnings fixed or justified in the log.

## Phase 2 — Footprints & library

- [ ] Each footprint verified against its datasheet land pattern (CRD TO-92, ADS1115
      package, connectors, R_ref). A wrong pinout here is silent and fatal.
- [ ] Courtyards present, non-overlapping; 3D models attached.
- [ ] All symbols/footprints in project-local `libraries/`, not global libs.

## Phase 3 — Board setup & layout

- [ ] Board-setup constraints match the target fab (track/space, drill, annular ring) — set
      **before** routing so DRC is meaningful.
- [ ] **Netclasses:** `SENSE` (V_RTD pairs and V_ref pairs — precision analog), `POWER`,
      `I2C` (SDA/SCL), default. Route sense/V_ref as short tight pairs.
- [ ] **Mixed-signal partition (new and important):** I²C + ADS1115 digital side is switching
      traffic next to µV analog. Separate analog and digital ground regions with a single-
      point tie; keep SDA/SCL away from R_ref taps and the sense pairs; guard if needed.
- [ ] **Star ground** physically implemented: RTD force-returns + analog ground meet at one
      point; no long shared return trace between channels (`board_spec.md` §Layout-critical).
- [ ] **Each ADS1115 next to its two R_ref pairs;** V_ref input pairs as short as possible.
- [ ] **Sense-line RC filter** (≈1 kΩ + 0.1 µF differential) at the T7 input, sized to settle
      within the T7 mux dwell.
- [ ] Connector pinout sane and labeled; channel order matches silk and spec; polarity/keying.
- [ ] Mounting holes; fiducials if machine-assembled; readable silk (channels, test points,
      I²C addresses, rev).
- [ ] **DRC clean: 0 violations** against configured rules; zones refilled before export.

## Phase 4 — Review & outputs

- [ ] Generate and **look at**: schematic PDF, 3D render, BOM, DRC report.
- [ ] Cross-check BOM vs `board_spec.md` — CRD count = channels, ADS1115 count = ceil(ch/2),
      R_ref count = channels, pull-ups/decoupling present.
- [ ] No unrouted net; no stray ratsnest; no DNP that should be populated.
- [ ] Don't trust auto-placement/route — review every net, especially sense/V_ref separation,
      the star ground, and the analog/digital partition.
- [ ] Tag the reviewed state (`rev-A`) before generating the gitignored `fab/` drop.

---

## Cross-cutting principles
- **Traceability:** every value has a reason in `board_spec.md` or the log.
- **Verify, don't assume:** re-run gates after every change.
- **Small reversible steps + commit per checkpoint.**
- **Tiebreaker:** when a layout choice is ambiguous, choose the option that best protects the
  precision-analog path (sense + V_ref) and keeps the I²C/digital side off it. The board's
  whole purpose is a quiet, position-independent, ratiometric measurement.

## Canonical gate commands

```bash
kicad-cli sch erc --exit-code-violations --severity-error \
  --format json --output reports/erc/erc_sNNN.json hardware/rtd-readout.kicad_sch

kicad-cli pcb drc --exit-code-violations --severity-error \
  --format json --output reports/drc/drc_sNNN.json hardware/rtd-readout.kicad_pcb

kicad-cli sch export bom \
  --fields "Reference,Value,Footprint,MPN,Manufacturer,Tolerance,Tempco,Datasheet" \
  --group-by "Value,Footprint" --sort-field Reference --exclude-dnp \
  --output reports/bom/bom_sNNN.csv hardware/rtd-readout.kicad_sch

kicad-cli sch export netlist --output sim/netlists/rtd-readout.net hardware/rtd-readout.kicad_sch

# Manufacturing drop (only at a tagged rev; fab/ is gitignored)
kicad-cli pcb export gerbers --output fab/gerbers/ hardware/rtd-readout.kicad_pcb
kicad-cli pcb export drill   --output fab/drill/   hardware/rtd-readout.kicad_pcb
kicad-cli pcb export pos     --output fab/pos/      hardware/rtd-readout.kicad_pcb
kicad-cli pcb export step    --output fab/rtd-readout.step hardware/rtd-readout.kicad_pcb
```

A phase is done only when its gate exits clean, the result is written to `reports/`, and it's
cited in the session log.
