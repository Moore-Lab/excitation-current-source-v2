# TESTING_PLAN.md

Two-part verification for the REF200 RTD board, plus a shared report format.

- **Part 1 — SPICE (Claude Code runs):** prove the circuit is correct and quantify the
  accuracy/noise budget *before* fabrication.
- **Part 2 — Bench (Lucas runs):** staged bring-up with go/no-go gates, ending in the
  measurement that actually matters — position-independent, quiet readings.

Acceptance criteria are tied to the original problem: the board must (a) deliver a known,
stable per-channel current, (b) recover R to an accuracy set by the reference resistor,
not the REF200, and (c) show **no channel/position dependence** in the noise — the failure
mode of the old series chain.

---

## Part 1 — SPICE verification (ngspice, batch)

### Model strategy

- Look for a TI SPICE/PSpice model for the REF200 (product page). If one exists, place it
  in `sim/models/` and use it.
- If not, model each 100 µA section as an **ideal DC current source in parallel with a
  finite output resistance** (datasheet output impedance 20–100 MΩ; use ~50 MΩ). Parallel
  two for the 200 µA mode. For noise work, add an explicit current-noise source calibrated
  to the datasheet (1 nA p-p over 0.1–10 Hz; 20 pA/√Hz at 10 kHz) since an ideal source is
  noiseless in `.noise`.
- RTD = a resistor swept across its operating range (Pt100: ~80–157 Ω; Pt1000: ~800–1570 Ω).
- R_ref = the chosen precision value; vary it for tolerance/tempco studies.
- Run headless: `ngspice -b deck.cir -o reports/sim/<test>.log` and parse the output; have
  a python script in `sim/scripts/` produce plots into `reports/sim/`.

### Test cases (each → a deck in `sim/netlists/`, a result + report in `reports/sim/`)

1. **DC operating point & compliance margin.** Sweep RTD across its range at nominal and
   worst-case supply. *Pass:* voltage across each REF200 source stays ≥ 2.5 V (target
   ≥ 3 V margin) at the highest RTD resistance and lowest supply.
2. **Ratiometric correctness (sanity).** Sweep RTD; compute `R_calc = R_ref·V_RTD/V_ref`.
   *Pass:* `R_calc` equals the swept RTD value to within numerical error — confirms the
   topology and that the result is independent of the source value.
3. **Accuracy / Monte Carlo (the key deliverable).** Vary R_ref by its tolerance and over
   the expected board ΔT (tempco), include source-current variation and an assumed ADC
   offset/gain. Propagate to an **equivalent temperature error in °C** for the chosen RTD.
   *Pass:* total error dominated by R_ref, within the target budget (for 0.01 % / 10 ppm
   over ~10 °C this should land well under ±0.1 °C from the reference resistor; state the
   computed number).
4. **Compliance corner.** Max RTD R + min supply + tolerances. *Pass:* still in compliance.
5. **Transient — sense RC settling.** Step the sense node and measure settling of the
   ~1 kΩ/0.1 µF filter. *Pass:* settles to < ½ ADC LSB within the planned T7 mux dwell.
   This sizes the filter R/C and the scan rate together (ties to the "mux settling" risk).
6. **Noise (`.noise`).** Sum REF200 current-noise (×R) and Johnson noise of R_ref+RTD,
   band-limited by the RC filter, referred to the ADC input. *Pass:* total excitation +
   passive-chain noise is **below the T7 ADC noise floor** — i.e. the excitation is not
   the limiter (expected: ~100 nV-level vs mV signals). This confirms the architecture
   targets the real problem (CMRR/series stacking) without introducing a new noise source.
7. **Crosstalk (optional but recommended).** Model two channels sharing a finite
   star-ground return impedance; perturb one channel's current. *Pass:* coupling into the
   other channel's reading is below the noise floor for the planned ground resistance —
   use it to set the acceptable star-ground trace resistance.

Each test writes a report (next section) with measured-vs-expected and an explicit
pass/fail against its criterion. Failures block fabrication.

---

## Part 2 — Bench verification (real board)

Staged bring-up. **Each stage is a go/no-go gate; do not proceed past a failure.** Probe
the test points added per `BOARD_DEV_CHECKLIST.md`. Handle the REF200 with ESD precautions
(it is only ±750 V CDM rated) — wrist strap, grounded mat.

- **Stage 0 — Power off, inspection.** Visual check; DMM continuity for shorts on the rail
  and between force/sense nets; confirm no solder bridges on the REF200. *Gate:* no shorts.
- **Stage 1 — Power tree.** Bring up the LDO with the REF200 **not yet in circuit** (or
  outputs open). *Gate:* clean +5 V (or +3.3 V) within tolerance, low ripple.
- **Stage 2 — Current verification & per-channel calibration.** With a known precision
  resistor (or DMM in current mode) at each channel output, measure the actual delivered
  current. Record each channel's value — **this is the calibration constant** for the
  calibrated-current measurement mode. *Gate:* each channel within REF200 spec and stable.
- **Stage 3 — Ratiometric accuracy (substitution).** Replace RTDs with precision resistors
  or a decade box across the RTD range. Read V_ref and V_RTD on the T7; compute
  `R_ref·V_RTD/V_ref`. *Gate:* recovered R matches the known resistor across the range,
  within the SPICE-predicted budget.
- **Stage 4 — Compliance headroom.** At the largest resistance, confirm the channel still
  regulates (voltage doesn't collapse). *Gate:* in compliance.
- **Stage 5 — Real RTDs, two-point.** Connect the actual 4-wire RTDs. Ice bath (0 °C → R0)
  and a second known temperature against a reference thermometer. *Gate:* both points
  within budget; Kelvin sensing confirmed (vary lead length and see no shift).
- **Stage 6 — Noise & position independence (the headline test).** At a fixed, stable
  temperature, record noise on every channel. *Gate:* (a) per-channel noise at or below
  the T7 + Johnson floor, and (b) **no dependence on channel/position** — directly compare
  against the old series-chain data where noise grew up the chain. This is the test the
  whole redesign exists to pass.
- **Stage 7 — Crosstalk.** Perturb one channel (e.g. warm one RTD); confirm the others
  don't move beyond noise. *Gate:* no measurable cross-coupling.
- **Stage 8 — Thermal soak / drift.** Log all channels for hours at fixed temperature.
  *Gate:* drift within budget; confirm R_ref tempco dominates as predicted (not the
  REF200, not grounding).

Bench data lands in `test/data/` (committed — it can't be regenerated). Each stage gets a
report.

---

## Report format (both SPICE and bench)

One markdown report per test/stage in `reports/sim/` or `reports/test/`, using the same
skeleton so they're comparable:

```
# <Test/Stage name> — <date> — <sim | bench>

## Objective
<what this test proves, and which acceptance criterion it maps to>

## Setup
<deck file / instruments, T7 config (range, resolution index), DUT, conditions>

## Method
<exact steps / command run / sweep parameters>

## Results
<table: quantity | expected | measured | unit>
<plots: link to figure files>

## Pass / Fail
<criterion stated, then PASS or FAIL with the margin>

## Anomalies & notes
<anything unexpected; deviations from prediction>

## Next
<follow-up action, if any>
```

After running a test, Claude Code records the pass/fail and report path in the session log
under **Validation**. A SPICE failure blocks the fab drop; a bench failure blocks sign-off
on that rev and feeds back into a new session objective.
