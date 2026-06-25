# RTD Readout Board — User Manual (rev-A)

**One document to understand the board, see exactly what was built, and judge whether it
makes sense.** It covers the design rationale, the as-built configuration, the verification
evidence (with commands to reproduce), how to order and assemble it, and how to calibrate,
operate, and bench-test it.

- **Design source of truth:** [`board_spec.md`](board_spec.md) (electrical). This manual
  explains and summarizes it; if the two ever disagree, `board_spec.md` wins.
- **Hardware revision:** `rev-A` (git tag). Manufacturing drop: tag `fab-rev-A`.
- **Status:** Design complete and verified in simulation; **not yet fabricated or bench-tested.**

---

## 1. What the board does (in one paragraph)

It reads up to 7 four-wire RTDs using a LabJack T7 Pro whose 7 differential analog pairs are
*already* committed to measuring RTD voltages. Each RTD gets its own constant-current loop so
it sits near ground (killing the position-dependent common-mode noise a series chain caused),
and the excitation current is measured **live** so the current source's accuracy and drift
never enter the result. The trick that makes it fit with zero spare analog channels: the
current-sense voltage is digitized **on the board** by I²C ADCs (ADS1115) on the T7's digital
lines, not on an analog pair. **This build is populated for Pt100, 3 channels.**

---

## 2. How the circuit works

### 2.1 The per-channel signal chain

Each channel is one series current loop. The same current `I` flows through every element:

```
   +5 V rail
      │
   [ CRD ]            current-regulator diode, ~0.22 mA (CDLL5283). The current source.
      │  I  (identical current through everything below)
  TOP ●───────────────► ADS1115 IN+   ┐  V_ref read differentially, on-board, over I²C
   [ R_ref ]  910 Ω                    │
  MID ●───────────────► ADS1115 IN−   ┘
      │  Force+
      ▼
   [ RTD, 4-wire ]    Sense+ ●────────► T7 AINx+  ┐  V_RTD on the existing T7 diff pair
                      Sense− ●────────► T7 AINx−  ┘  (Kelvin, full 4-wire)
      │  Force−
      ▼
   STAR GND
```

### 2.2 The key idea: measure the current, don't trust it

To get temperature you need the RTD's resistance, `R = V/I`. Instead of needing a precise,
stable current, this design puts a **reference resistor `R_ref` in series with the RTD**, so
the *same* current flows through both. Then:

- Current through both: `I = V_ref / R_ref`
- RTD resistance: `R_RTD = V_RTD / I = R_ref · (V_RTD / V_ref)`

**The current cancels.** This is a *ratiometric* measurement. As a result the CRD's ±10 %
tolerance, its tempco, and its channel-to-channel spread are **irrelevant** — it only has to
hold steady and quiet for the few milliseconds of one scan.

### 2.3 The twist: two ADCs, joined by one calibration constant

`V_RTD` is read by the T7. There is no spare analog channel for `V_ref`, so `V_ref` is
digitized **on the board** by an **ADS1115** that reports over **I²C** (the T7's digital
lines). That is what makes the design fit with zero spare analog channels — but it means
`V_RTD` and `V_ref` are measured by two *different* converters with different gains:

```
V_RTD_meas / V_ref_meas = (G_T7 / G_ADS) · (R_RTD / R_ref)
```

Fold **everything constant** — `R_ref`'s value, the gain ratio `G_T7/G_ADS`, fixed offsets —
into a single per-channel calibration constant **C**:

```
R_RTD = C · (V_RTD_meas / V_ref_meas)
```

Measure `C` **once per channel** by substituting a known precision resistor for the RTD:

```
C = R_known · (V_ref_meas / V_RTD_meas) │ measured with R_known in place of the RTD
```

Because `C` absorbs `R_ref`'s value, **`R_ref`'s absolute tolerance does not matter** either —
you pay for its *stability* (≤10 ppm/°C tempco), not its accuracy.

### 2.4 What actually limits accuracy (after cross-cal)

1. The `R_known` used at calibration time (use a 0.01 % part — once).
2. `R_ref` tempco drift between recalibrations.
3. The **relative gain drift of the two ADCs** (`G_T7/G_ADS`) between recalibrations.

Keep both converters thermally stable and recalibrate periodically. Feel for the budget
(Pt100): a fractional ratio error shows up as ≈ `260 ×` that error in °C, so ~100 ppm of
combined drift ≈ 0.026 °C.

### 2.5 Why the RTD sits at the bottom of each loop

Each RTD has its **own** loop with the RTD just above star ground, keeping it near ground
potential → low common-mode → no position-dependent noise. (The previous design chained RTDs
in series, floating them to large common-mode levels — the noise this redesign exists to
kill.) All `Force−` returns meet at **one star-ground point** so no channel's return current
flows through another's path. The RTD is wired **4-wire Kelvin**: separate Force (current) and
Sense (voltage) wires, so lead resistance carries current but isn't measured.

---

## 3. As-built configuration (this board)

Locked inputs (Session 002): **Pt100, 3 of the 7 T7 pairs are RTDs.**

| Item | Value | Why |
|------|-------|-----|
| RTD type | Pt100 | → T7 range ±0.1 V (≈18–35 mV at ~0.22 mA) |
| Channels | 3 | sets the repeated-hardware counts below |
| CRD | CDLL5283, ~0.22 mA | current source; value unimportant (measured live) |
| R_ref | 910 Ω, ≤10 ppm/°C | V_ref ≈ 200 mV nominal, ≈ 220 mV at +10 % CRD |
| ADS1115 range | ±0.256 V | V_ref ≈ 86 % of full scale at worst case (no clip) |
| ADS1115 count | 2 (0x48, 0x49) | 1 chip per 2 channels → ceil(3/2); ch3 uses one input of U2, one spare |

Rough operating numbers: `V_ref ≈ 910 Ω × 0.22 mA ≈ 200 mV`; Pt100 (≈100–138 Ω over 0–100 °C)
→ `V_RTD ≈ 22–30 mV`. Only the `V_RTD` (Sense±) lines leave as analog; `V_ref` never leaves the
board as analog.

---

## 4. Bill of materials (verified against `board_spec.md`)

Exported from the schematic; counts cross-checked against the spec's rules.

| Refdes | Qty | Part | Notes |
|--------|-----|------|-------|
| D1–D3 | 3 | CRD ~220 µA (CDLL5283) | = channels |
| R1–R3 | 3 | 910 Ω ≤10 ppm/°C thin-film | R_ref; pay for tempco, not tolerance |
| R4,R5 | 2 | 4.7 kΩ | I²C pull-ups (SDA, SCL) |
| U1,U2 | 2 | ADS1115IDGS | 0x48 (ADDR→GND), 0x49 (ADDR→VS) |
| C1,C2 | 2 | 0.1 µF | per-chip decoupling |
| C3,C4 | 2 | 10 µF | bulk on +5V / VS |
| J1–J3 | 3 | 4-pos 5.08 mm screw terminal | RTD 4-wire (Phoenix MKDS) |
| J4 | 1 | 2×4 header | to T7 analog (3 Sense± pairs + AGND) |
| J5 | 1 | 1×4 header | to T7 I²C (SDA/SCL/VS/GND) |
| J6 | 1 | 2-pos screw terminal | power in (+VIN/GND) |
| TP1–TP10 | 10 | test pads | TOP/MID/rail/GND/SDA/SCL taps |

**Total: 30 components.** Count rules all pass: CRD = channels (3), R_ref = channels (3),
ADS1115 = ceil(3/2) (2), pull-ups + decoupling + bulk present. Detail:
[`reports/review/BOM_REVIEW.md`](../reports/review/BOM_REVIEW.md).

> Note: generic passives (C1–C4, R4/R5, headers) carry placeholder MPNs — assign at order
> time. Precision parts (CRD, R_ref, ADS1115, terminals) are fully specified.

---

## 5. Board & layout

- **4 copper layers** (F.Cu, In1.Cu, In2.Cu, B.Cu), **1.6 mm** thickness, board outline defined.
- **Design rules** (standard-fab manufacturable):

  | Netclass | Track | Via (Ø/drill) | Clearance |
  |----------|-------|---------------|-----------|
  | Default / I2C / SENSE | 0.25 mm | 0.6 / 0.3 mm | 0.13 mm |
  | POWER | 0.50 mm | 0.8 / 0.4 mm | 0.13 mm |

  Board minimums: 0.13 mm track, 0.2 mm hole.

- **Layout-critical points** (the analog-integrity rules the layout honors):
  - **Star ground** — all RTD `Force−` returns + analog ground meet at one point.
  - **RTD at the bottom of each loop** — low common-mode (the reason the board exists).
  - **Mixed-signal partition** — I²C/digital kept away from the µV-level R_ref taps and Sense
    pairs; analog/digital grounds joined at a single point; every ADS1115 decoupled.
  - Each ADS1115 next to its two R_ref pairs; V_ref routed as a tight, short differential pair.
  - 4-wire Kelvin preserved to each RTD; light sense-line RC filter at the T7 input.

Full fab-readiness summary: [`reports/review/FAB_READINESS.md`](../reports/review/FAB_READINESS.md).

---

## 6. Interfaces & connectors

| Connector | Goes to | Signals |
|-----------|---------|---------|
| J1–J3 | the RTDs | Force+, Force−, Sense+, Sense− (4-wire, per RTD) |
| J4 | T7 analog (CB37) | 3× Sense± pairs (V_RTD) + AGND. **Only analog lines that leave the board.** |
| J5 | T7 digital | SDA, SCL, VS, GND (I²C) |
| J6 | power supply | +VIN (5 V), GND |

**Test points (TP1–TP10):** each TOP node, each MID/Sense+ node, the rail, GND, SDA, SCL —
use these for the bench stages in §10.

---

## 7. Where everything lives (repository map)

```
hardware/        KiCad project — schematic (.kicad_sch), board (.kicad_pcb), project (.kicad_pro)  [SOURCE]
libraries/       project-local symbols + footprints (board builds identically on any machine)      [SOURCE]
sim/             SPICE decks, models, run_all.py harness                                            [SOURCE]
host/            acquisition code: T7 driver, ADS1115 I²C driver, time-aligned read, ratiometric    [SOURCE]
test/            staged bench procedures (import host/) + measured data/                            [SOURCE]
scripts/         kicad-cli gate wrappers: run_gates, fab_drop, erc, drc, export_bom                 [SOURCE]
reports/         ERC/DRC/SPICE/BOM/review artifacts (generated, committed)
fab/             gerbers/drill/pos/STEP/BOM (generated, gitignored, captured by tag fab-rev-A)
docs/            this manual, board_spec.md, testing/dev/parallel plans, per-track logs
```

Rule of thumb: if a command can regenerate a file, it's not source — it lives in `reports/`
(committed) or `fab/` (gitignored, tagged). See [`DIRECTORY_MANAGEMENT.md`](DIRECTORY_MANAGEMENT.md).

---

## 8. Verification evidence — *does this make sense?*

Everything below was re-run on the final merged design and can be reproduced with the commands
shown. Tooling: **KiCad 10.0.3**, **ngspice 44**.

### 8.1 Electrical rule checks (gates)

| Gate | Result | How to reproduce |
|------|--------|------------------|
| **ERC** (schematic) | **0 errors / 0 warnings** | `kicad-cli sch erc hardware/rtd-readout.kicad_sch` |
| **DRC** (board) | **0 violations / 0 unconnected** | `kicad-cli pcb drc hardware/rtd-readout.kicad_pcb` |
| Both, with report snapshots | pass | `sh scripts/run_gates --tag rev-A` |

There are **47 schematic-parity items** flagged by `--schematic-parity`. They are
**non-blocking and expected**: 30 "missing MPN field" + 10 "exclude-from-BOM differs"
(footprint metadata not back-synced from symbols — cosmetic) and 4 extra + 3 duplicate
footprints that are all *mounting holes / fiducials placed without a schematic symbol* (normal
for mechanical parts). **None are net/connectivity errors.**

### 8.2 SPICE — circuit correctness & accuracy budget (all 7 pass)

Reproduce: set `NGSPICE_BIN` to your ngspice console binary, then
`python sim/scripts/run_all.py`. Reports land in `reports/sim/*.md`.

| # | Test | Result | What it proves |
|---|------|--------|----------------|
| 1 | DC / CRD compliance | min V_CRD = 4.26 V (margin 3.21 V) | the CRD has enough voltage to regulate at worst case |
| 2 | Ratiometric + cross-cal | recovered-R error ~7×10⁻⁹ (tol 10⁻⁶) | the math works and is invariant to ±10 % CRD / R_ref perturbation |
| 3 | Monte-Carlo accuracy | σ ≈ 0.038 °C, tempco-dominated | accuracy is limited by R_ref + relative ADC gain tempco, as designed |
| 4 | R_ref sizing / no-clip | V_ref = 86 % FS, 14.8 effective bits | worst-case V_ref never clips the ADS1115 range |
| 5 | Sense-line settling | 1.02 ms < 5 ms mux dwell | the RC filter settles within the T7's dwell |
| 6 | Noise of the ratio | within target; **CRD noise bound 2.9 nA/√Hz** | the one architectural risk (CRD noise) is quantified and tolerable |
| 7 | Crosstalk vs star-ground R | 1.6×10⁻⁵ °C/Ω | sets the acceptable shared-ground resistance |

> A SPICE failure blocks fabrication; all 7 pass, and the re-run reproduced the committed
> results byte-identical (the circuit is unchanged from the verified version).

### 8.3 How to satisfy yourself the build is real

1. Open `hardware/rtd-readout.kicad_pro` in KiCad → inspect the schematic and the 4-layer board.
2. Run `sh scripts/run_gates` → confirm ERC/DRC pass on your machine.
3. Skim `reports/sim/*.md` → each test's objective, method, numbers, and pass margin.
4. Cross-read this manual's §2 (rationale) against `board_spec.md`.

---

## 9. Ordering & assembly

1. The manufacturing package is generated to `fab/` (gitignored) and captured by tag
   **`fab-rev-A`**. Regenerate any time with `sh scripts/fab_drop` (deterministic from the
   board): gerbers, drill, pick-and-place CSV, STEP, fab BOM.
2. Upload `fab/gerbers` + `fab/drill` to your fab; 4-layer, 1.6 mm, standard rules. Add
   panelization at the fab portal if required (the design is a single-board outline).
3. Assemble per the BOM (§4). The ADS1115 is ESD-sensitive — observe ESD care.
4. Strap the ADS1115 addresses: **U1 ADDR→GND (0x48)**, **U2 ADDR→VS (0x49)**.

---

## 10. Calibration & operation

### 10.1 Cross-calibration (do once per channel, then periodically)

For each channel, substitute a known **0.01 %** resistor for the RTD, read `V_RTD` (T7) and
`V_ref` (ADS1115) **time-aligned**, and store:

```
C = R_known · (V_ref_meas / V_RTD_meas)
```

`C` should be stable across repeats; channel-to-channel spread reflects CRD spread and is
absorbed by `C`. The acquisition + math live in `host/`.

### 10.2 Live operation

1. Read `V_RTD` on the T7 (±0.1 V range, high resolution index, adequate mux settling).
2. Read `V_ref` on the matching ADS1115 input over I²C; **average several conversions** to beat
   LSB noise on the small signal.
3. Apply `R_RTD = C · (V_RTD / V_ref)`, then convert R→°C with the Pt100 curve.
4. Recalibrate periodically (cadence set by Stage 7 thermal-soak results, §11).

---

## 11. Bench verification (Part 2 — run on the physical board)

Staged go/no-go gates (from [`TESTING_PLAN.md`](TESTING_PLAN.md)); bench data → `test/data/`.

| Stage | Gate |
|-------|------|
| 0 Inspection | no shorts on rail / force-sense / SDA-SCL |
| 1 Power & I²C bring-up | all ADS1115 addresses detected; V_ref sane & stable |
| 2 **Cross-calibration** | C stable across repeats |
| 3 Ratiometric accuracy | recovered R matches within the SPICE budget; Kelvin verified |
| 4 Real RTDs, two-point | ice bath (0 °C) + second known temp within budget |
| 5 **Noise & position independence** | per-channel noise at target **and no channel/position dependence** (the headline test) |
| 6 Crosstalk | warming one RTD doesn't move others beyond noise |
| 7 **Thermal soak** | C drift within budget (validates the R_ref + ADC-gain-tempco term; sets recal interval) |
| 8 CRD noise check | CRD noise over a scan below the floor (the source risk; if it fails, swap CRD for a reference+op-amp source — readout unchanged) |

---

## 12. Limitations & open items

- **Not yet fabricated or bench-tested.** Sections 8.1–8.2 are simulation + rule checks; the
  board is proven correct in design, not yet in hardware.
- **Bench Part 2 (§11) is pending** and requires the physical board — it includes the headline
  position-independence test the redesign exists to pass.
- **Generic-passive MPNs are placeholders** — assign before a production BOM pull.
- **No panelization** in the package (single-board outline).
- **CRD noise is the one architectural risk** (Stage 8). If hardware shows it's too high, the
  fix is a reference+op-amp current source; the ratiometric readout stays either way.
- **Recalibration cadence is TBD** until Stage 7 quantifies C drift.

---

## 13. Provenance

Built across parallel tracks A–G (libraries, SPICE, host/bench, automation, schematic, layout,
fab) and merged to `main`. Per-track detail in `docs/sessions/track*.md`; integration history in
[`SESSION_LOG.md`](SESSION_LOG.md). Hardware frozen at tag `rev-A`; fab drop at `fab-rev-A`.
