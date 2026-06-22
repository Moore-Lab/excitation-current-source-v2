# BOARD_DEV_CHECKLIST.md

What good PCB development looks like for this board. Use it as a gate list, not a
narrative — nothing advances to the next phase until the current phase's checks pass.
Items in **bold** are specific to *this* design and are the ones most likely to bite if
skipped. Everything traces back to `docs/board_spec.md`.

The canonical validation commands (the "gates") are at the bottom; cite their output in
the session log.

---

## Phase 1 — Schematic capture

- [ ] Every symbol has: value, footprint, MPN, manufacturer, datasheet link. A blank field
      now becomes a sourcing error at assembly.
- [ ] **The reference resistor is annotated as the precision part:** 0.01 %, ≤10 ppm/°C,
      with a real MPN. Do not let a generic 1 % resistor symbol stand in — it is the
      accuracy-limiting component of the whole board (`board_spec.md` §3).
- [ ] **REF200 strapped per the chosen current mode** (`board_spec.md` §2): pins 7+8 → rail
      and 1+2 → load for 200 µA one-channel; sources split for 100 µA two-channel. Mirror
      pins 3/4/5 left open. **Substrate pin 6 → GND.**
- [ ] **RTD sits at the bottom of each loop** (low side to star ground) so its differential
      common-mode stays at tens of mV — this is the entire reason the board exists. Verify
      the topology in schematic matches §1, not an accidental reordering.
- [ ] **Force and Sense are separate nets** all the way to the connector; the Kelvin
      junction is at the RTD, not on the board.
- [ ] Power flags / PWR_FLAG on the rail and ground so ERC doesn't false-flag, but no
      others hiding real problems.
- [ ] Net labels meaningful and per-channel-scoped (e.g. `CH1_FORCE+`, `CH1_SENSE+`).
- [ ] Decoupling on the LDO per its datasheet; LDO input from the existing supply, output
      a clean +5 V (or +3.3 V) rail — **no DC-DC buck** (`board_spec.md` §4).
- [ ] Optional reverse-protection diode (1N4148) across each source if hot-plug/fault is
      plausible (`board_spec.md` §2; datasheet Fig. 17a).
- [ ] **Test points placed in the schematic** (see Phase 3) — add them now so they get
      net-connected, not bolted on later.
- [ ] **ERC clean: 0 errors.** Every warning either fixed or justified in the log.

## Phase 2 — Footprints & library

- [ ] Each footprint verified against the component datasheet land-pattern (REF200 SOIC-8,
      resistor package, connector). A wrong pinout or pad here is silent and fatal.
- [ ] Courtyards present and non-overlapping; 3D models attached where available.
- [ ] All symbols/footprints live in project-local `libraries/` (see
      `DIRECTORY_MANAGEMENT.md`), not global libs.
- [ ] Footprint-to-symbol pin mapping checked (especially REF200 pin numbers vs the
      datasheet table in `board_spec.md` §2).

## Phase 3 — Board setup & layout

- [ ] **Board setup constraints match the target fab** (track/space, drill, annular ring).
      Set these *before* routing so DRC is meaningful.
- [ ] **Netclasses defined:** a `SENSE` class (the high-impedance-to-the-ADC measurement
      pairs), a `FORCE`/`POWER` class, and default. Sense pairs routed as matched
      differential-ish pairs, short, away from the rail and any switching.
- [ ] **Star ground implemented physically:** all RTD force-returns, LDO ground, and the
      board's ground reference meet at one defined point. Do not let channel returns share
      a long common trace — shared return impedance is exactly the crosstalk path
      (`board_spec.md` §6).
- [ ] **R_ref placed tight to its REF200, short traces, thermally quiet** — out of any
      airflow path and away from the LDO or anything that dissipates heat (its tempco is
      the accuracy limit).
- [ ] **Sense-line RC filter** (≈1 kΩ series + 0.1 µF differential, ~1.6 kHz) placed at the
      board's measurement output, sized so it settles within the T7 mux dwell
      (`board_spec.md` §6; quantify in the SPICE transient test).
- [ ] **Substrate (pin 6) tied to ground plane/star point.**
- [ ] **Test points** for: each channel's current node (top of R_ref), V_ref low node /
      RTD sense+, RTD sense−, the rail, and GND. These are what the bench plan probes —
      label them on silk.
- [ ] Connector pinout sane and labeled; channel order on the connector matches silk and
      the spec; polarity/keying marked.
- [ ] Mounting holes; fiducials if the board will be machine-assembled.
- [ ] Silk legends readable: channel numbers, test-point names, polarity, rev.
- [ ] **DRC clean: 0 violations** against the configured rules. Zones refilled before any
      export.

## Phase 4 — Review & outputs

- [ ] Generate and **actually look at**: schematic PDF, 3D render, BOM, DRC report.
- [ ] Cross-check the BOM against `board_spec.md` §7 — quantities, the precision R_ref,
      REF200 count consistent with the current mode and channel count.
- [ ] No net left unrouted; no DNP that should be populated; no ratsnest remaining.
- [ ] Do not blindly trust any auto-placement/auto-route — review every net, especially
      sense/force separation and the star ground.
- [ ] Tag the reviewed state (`rev-A`) before generating the gitignored `fab/` drop.

---

## Cross-cutting principles

- **Traceability:** every value on the board has a reason in `board_spec.md` or the log.
  If you can't point to the reason, you don't yet understand the choice.
- **Verify, don't assume:** re-run gates after every change; never report a pass you
  didn't observe this session.
- **Small reversible steps + commit per checkpoint.** A broken intermediate state is fine
  on a branch; a broken committed `main` is not.
- **The board's whole purpose is a quiet, position-independent measurement.** When a layout
  choice is ambiguous, choose the option that best protects the sense path and the star
  ground. That is the tiebreaker.

## Canonical gate commands

```bash
# Schematic ERC — nonzero exit on errors
kicad-cli sch erc --exit-code-violations --severity-error \
  --format json --output reports/erc/erc_sNNN.json hardware/ref200-rtd.kicad_sch

# PCB DRC — nonzero exit on violations
kicad-cli pcb drc --exit-code-violations --severity-error \
  --format json --output reports/drc/drc_sNNN.json hardware/ref200-rtd.kicad_pcb

# BOM (CSV) for review against board_spec.md §7
kicad-cli sch export bom \
  --fields "Reference,Value,Footprint,MPN,Manufacturer,Tolerance,Datasheet" \
  --group-by "Value,Footprint" --sort-field Reference --exclude-dnp \
  --output reports/bom/bom_sNNN.csv hardware/ref200-rtd.kicad_sch

# Netlist for SPICE / cross-checks
kicad-cli sch export netlist --output sim/netlists/ref200-rtd.net hardware/ref200-rtd.kicad_sch

# Manufacturing drop (only at a tagged rev; fab/ is gitignored)
kicad-cli pcb export gerbers --output fab/gerbers/ hardware/ref200-rtd.kicad_pcb
kicad-cli pcb export drill   --output fab/drill/   hardware/ref200-rtd.kicad_pcb
kicad-cli pcb export pos     --output fab/pos/      hardware/ref200-rtd.kicad_pcb
kicad-cli pcb export step    --output fab/ref200-rtd.step hardware/ref200-rtd.kicad_pcb
```

A phase is "done" only when its gate exits clean and the result is written to `reports/`
and cited in the session log.
