# TESTING_PLAN.md

Two-part verification plus a shared report format.

- **Part 1 — SPICE (Claude Code runs):** prove the circuit is correct and quantify the
  accuracy/noise budget before fabrication.
- **Part 2 — Bench (Lucas runs):** staged bring-up with go/no-go gates, ending in the
  measurement that matters — position-independent, quiet readings.

Because the design is ratiometric across **two ADCs** (T7 for V_RTD, ADS1115 for V_ref) and
self-calibrated, the acceptance criteria are: (a) the CRD delivers a stable, quiet current
over a scan; (b) after one-time **cross-calibration**, recovered R matches a known resistor;
(c) accuracy holds over temperature, limited by R_ref tempco + **relative ADC gain tempco**,
not by the source; and (d) **no channel/position dependence** in the noise.

---

## Part 1 — SPICE verification (ngspice, batch)

### Model strategy
- **CRD:** model as a current source in parallel with its finite dynamic impedance (the
  J500-class low-current parts sit high, ~MΩ-range Zt) plus a current-noise source
  (JFET-style; treat as the unknown to bound). The CRD's absolute value and tempco are
  intentionally not trusted — sweep them to confirm they cancel.
- **R_ref:** the chosen value; vary by tempco over board ΔT for the budget.
- **RTD:** resistor swept over range (Pt100 ~80–157 Ω; Pt1000 ~800–1570 Ω).
- **Two ADCs:** represent V_RTD and V_ref measurements with independent gain terms `G_T7`,
  `G_ADS` so the gain-ratio and its tempco can be injected.
- Run headless: `ngspice -b deck.cir -o reports/sim/<test>.log`; python in `sim/scripts/`
  produces plots into `reports/sim/`.

### Test cases (each → deck in `sim/netlists/`, report in `reports/sim/`)
1. **DC op & CRD compliance.** Sweep RTD at nominal and worst-case supply. *Pass:* voltage
   across the CRD stays above its limiting voltage `VL` at the highest RTD R and lowest rail.
2. **Ratiometric + cross-cal correctness.** Compute C from a modeled known resistor, then
   `R_calc = C·V_RTD/V_ref` across the RTD sweep. *Pass:* `R_calc` equals the swept value,
   and is **invariant** when the CRD current and R_ref absolute value are perturbed ±10 %.
3. **Accuracy / Monte-Carlo (key deliverable).** Vary R_ref tempco, the **relative ADC gain
   tempco (G_T7/G_ADS)**, and residual offsets over the expected board ΔT. Propagate to an
   **equivalent °C error** (Pt100: ≈260×fractional). *Pass:* dominated by R_ref + relative
   gain tempco, within target (~0.03–0.05 °C for ~10 ppm/°C parts over ~10 °C — confirm).
4. **R_ref sizing / no-clip.** Confirm worst-case V_ref (max CRD current + R_ref tol) stays
   under the chosen ADS1115 range. *Pass:* < ~90 % of full-scale, with good effective bits.
5. **Transient — sense RC settling.** Step the sense node; confirm the ~1 kΩ/0.1 µF filter
   settles to < ½ T7 LSB within the mux dwell.
6. **Noise of the ratio.** Combine CRD current-noise (×R), Johnson noise of R_ref+RTD, T7
   noise on V_RTD, and ADS1115 noise on V_ref, band-limited. *Pass:* the ratio's noise sits
   below the per-channel resolution target — **and explicitly bound the CRD noise**, since
   that is the one source weakness this architecture tolerates only if it's small enough.
7. **Crosstalk (recommended).** Two channels sharing a finite star-ground return impedance;
   perturb one. *Pass:* coupling below the noise floor — sets the acceptable ground resistance.

A SPICE failure blocks fabrication.

---

## Part 2 — Bench verification (real board)

Staged, each a go/no-go gate. Probe the test points from `BOARD_DEV_CHECKLIST.md`. ESD care
on the ADS1115.

- **Stage 0 — Power off, inspection.** Continuity; no shorts on rail or between force/sense
  or SDA/SCL. *Gate:* no shorts.
- **Stage 1 — Power & I²C bring-up.** Bring up the rail; confirm clean supply; scan the I²C
  bus and **detect all ADS1115 addresses (0x48–0x4B)**; read each V_ref channel raw.
  *Gate:* all chips present, V_ref sane and stable.
- **Stage 2 — Cross-calibration (replaces current calibration).** For each channel,
  substitute a known 0.01 % resistor for the RTD; read V_RTD (T7) and V_ref (ADS1115)
  time-aligned; compute and store **C = R_known·(V_ref/V_RTD)**. *Gate:* C stable across
  repeats; channel-to-channel spread as expected from CRD spread (and absorbed by C).
- **Stage 3 — Ratiometric accuracy.** Sweep known resistors / a decade box across the RTD
  range; compute `R = C·V_RTD/V_ref`. *Gate:* recovered R matches within the SPICE-predicted
  budget; verify Kelvin (vary lead length → no shift).
- **Stage 4 — Real RTDs, two-point.** Ice bath (0 °C → R0) and a second known temperature vs
  a reference thermometer. *Gate:* both within budget.
- **Stage 5 — Noise & position independence (headline).** At fixed temperature, record noise
  on every channel. *Gate:* (a) per-channel noise at/below the resolution target, and (b)
  **no dependence on channel/position** — compare directly against the old series-chain data.
  This is the test the redesign exists to pass.
- **Stage 6 — Crosstalk.** Perturb one channel (warm one RTD); others must not move beyond
  noise. *Gate:* no measurable coupling.
- **Stage 7 — Thermal soak (validates the new accuracy term).** Soak for hours at fixed
  temperature and watch **C drift** — this directly measures the R_ref + relative-ADC-gain-
  tempco term and tests the "keep both ADCs thermally stable" assumption. *Gate:* drift
  within budget; if C drifts more than predicted, improve thermal coupling of the two ADCs or
  shorten the recal interval.
- **Stage 8 — CRD noise check (the source risk).** Confirm on hardware that CRD noise over a
  scan is below the floor — the one thing that, if it fails, forces swapping the CRD for a
  reference+op-amp source. The ratiometric readout stays either way.

Bench data → `test/data/` (committed). Each stage gets a report.

---

## Report format (SPICE and bench)

One markdown report per test/stage in `reports/sim/` or `reports/test/`, same skeleton:

```
# <Test/Stage> — <date> — <sim | bench>
## Objective        (what it proves; which acceptance criterion)
## Setup            (deck/instruments; T7 range + resolution index; ADS1115 PGA range; DUT)
## Method           (exact steps / command / sweep params)
## Results          (table: quantity | expected | measured | unit; plots)
## Pass / Fail      (criterion, then PASS/FAIL with margin)
## Anomalies & notes
## Next
```

After a test, record pass/fail and the report path in the session log under **Validation**. A
SPICE failure blocks the fab drop; a bench failure blocks sign-off on that rev and becomes a
new session objective.
