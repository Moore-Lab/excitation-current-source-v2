# board_spec.md — RTD Readout Board

Electrical design source of truth. Every component value and layout choice traces back
here. The companion process docs (`PARALLEL_PLAN.md`, the track briefs, the checklist,
the testing plan) implement what this file specifies.

## What the board does

Reads up to 7 four-wire RTDs on an existing LabJack T7 Pro whose 7 differential analog
pairs are **all already committed to the RTD voltage measurements**. Each RTD gets its own
constant-current loop (so it sits near ground — this kills the common-mode/position-
dependent noise that a series chain produced), and the per-channel excitation current is
measured **live** so the source's accuracy and drift never enter the result.

The trick that makes it fit with zero spare analog channels: the current-sense voltage is
digitized on the board by I²C ADC(s) on the T7's digital lines, not on an analog pair.

## Signal chain, per channel

```
   +V rail (5 V; higher improves CRD regulation if available)
      │
   [ CRD ]            current-regulator diode, ~100 µA (SEMITEC S-101T, SMD), two-terminal
      │  I (same current through everything below)
  TOP ●───────────────► ADS1115 IN+   ┐ V_ref read differentially on-board, over I²C
   [R_ref]                            │
  MID ●───────────────► ADS1115 IN−   ┘
      │  Force+  (to RTD)
      ▼
   [ RTD 4-wire ]   Sense+ ●─────────► T7 AINx+  ┐ V_RTD on the existing T7 diff pair
                    Sense− ●─────────► T7 AINx−  ┘ (Kelvin, full 4-wire)
      │  Force−
      ▼
   STAR GND
```

## The measurement

The same current `I` flows through `R_ref` and the RTD. V_RTD is measured by the T7;
V_ref is measured by an ADS1115. Because they are on **different ADCs**, the raw ratio
carries the ratio of the two converters' gains:

    V_RTD_meas / V_ref_meas = (G_T7 / G_ADS) · (R_RTD / R_ref)

Fold everything constant into a single per-channel calibration constant **C**:

    R_RTD = C · (V_RTD_meas / V_ref_meas)

Measure C once by substituting a known resistor for the RTD:

    C = R_known · (V_ref_meas / V_RTD_meas)│_known

C absorbs `R_ref`'s value, the gain ratio, and any fixed offsets. Consequences:

- The CRD's ±10 % tolerance, tempco, and channel-to-channel spread are **irrelevant** —
  the current is measured live and cancels.
- `R_ref`'s **absolute value is irrelevant** (absorbed into C). Only its **stability**
  (tempco, low noise) matters.
- The accuracy limiters after cross-cal are: (1) the `R_known` used at calibration time
  (a 0.01 % part, used once), (2) `R_ref` tempco between recals, and (3) the **relative
  gain tempco of the two ADCs** between recals. Keep both converters thermally stable and
  recalibrate periodically.

Sensitivity, as a feel for the budget (Pt100): a fractional error `ΔI/I`-equivalent in the
ratio shows up as ≈ `260 · (error)` °C. So ~100 ppm of combined drift ≈ 0.026 °C.

## Components

### Current source — CRD (current-regulator diode)
- **SEMITEC S-101T, SMD flat 2-lead**, ~0.10 mA typical, band 0.05–0.21 mA guaranteed
  (−50 %/+110 %), Vk 0.5 V max, 100 V, 500 mW.
  *rev-F (2026-07-11):* current lowered ~2.4× (from the rev-E 0.24 mA J500) because the
  Pt100s sit **in vacuum in a cryostat (down to ~100 K)** where self-heating cannot
  convect away — at 100 µA the sensor dissipates ~0.3–1.6 µW (~6× less). The S-101T's
  huge band and up-to-+2.1 %/°C Ip tempco are cancelled by the ratiometric readout —
  stability burden sits on R_ref and the ADC gain ratio, not the CRD.
  Anode → rail, cathode → R_ref.
- Exact current is unimportant (measured live). It must only be **stable over one scan**
  and quiet. Compliance: needs a few volts across it to regulate; on a 5 V rail with
  ~0.25 V of load drop it sees ~4.7 V — verify against the chosen CRD's limiting voltage
  `VL`. A higher rail (e.g. 12 V) raises its dynamic impedance; CRD dissipation is trivial
  (~mW).

### Reference resistor R_ref
- Stable, low-tempco (≤10 ppm/°C), low-noise. **Absolute tolerance does not matter**
  (cross-cal absorbs it) — do not pay for 0.01 % here; pay for tempco and stability.
- **Size R_ref to the ADS1115 input range, not to the RTD.** Target V_ref near full-scale
  of the chosen PGA range, with margin for the CRD's +10 % spread so it never clips.
  Default (rev-F, sized for the S-101T band): **R_ref = 1.00 kΩ, ±0.05 %, ±2 ppm/°C**
  (Vishay TNPU12061K00AWEN00 bulk-thin-film) → V_ref ≈ 100 mV nominal, ≤ 210 mV (82 % FS)
  at the 0.21 mA band max — never clips the ADS1115 **±0.256 V** range (7.8125 µV/LSB).
  At ±2 ppm/°C the reference is deliberately **no longer the drift limiter** (ADC gain
  tempco and offset drift are); this is the rev-F stability-first policy: precision parts
  everywhere in the measurement path (2 ppm R_ref, 0.1 %/25 ppm thin-film filter R's,
  C0G/NP0 sense capacitors), ordinary grades for rails and digital.

### Current-sense ADC — ADS1115 (I²C)
- 16-bit, programmable-gain, I²C, four selectable addresses (0x48–0x4B via the ADDR pin).
  Two true differential inputs per chip (AIN0-1, AIN2-3). **7 channels → 4 chips → 8
  differential V_ref reads** on a single 2-wire bus.
- Read V_ref **differentially** at the R_ref pads. The V_ref common-mode (≈ V_RTD + V_ref/2,
  a few hundred mV) is well within the ADS1115's GND–VDD input range.
- Supply 3.3–5 V (e.g. from the T7's VS); add per-chip decoupling and bus pull-ups
  (4.7 kΩ typical; 2.2 kΩ if the bus is long/fast). Average several conversions per read to
  beat the LSB noise on the small signal.

### RTD voltage — existing T7 Pro pairs
- V_RTD on each RTD's existing differential pair, Kelvin-sensed at the RTD. Range: **±0.1 V**
  for Pt100 (≈3–16 mV at ~100 µA, 100 K floor), **±1 V** for Pt1000 (≈80–157 mV at 100 µA). Set the resolution
  index high and give each channel adequate mux settling.

## Board as the hub / interfaces

The board is the measurement hub. It takes the RTDs in, forms each current loop with a CRD
and R_ref, digitizes V_ref locally on the ADS1115s, and routes outward:
- **RTD connectors:** 4-wire (Force+, Force−, Sense+, Sense−) per RTD.
- **To the T7 analog (CB37):** the 7 Sense± pairs (V_RTD). Only these analog lines leave the
  board; V_ref never travels as analog.
- **To the T7 digital (I²C):** SDA, SCL, VS, GND.
- **Power in:** to the rail/LDO.

## Layout-critical points (full list in BOARD_DEV_CHECKLIST.md)
- **Star ground:** all RTD Force− returns and the analog ground meet at one point. Shared
  return impedance between channels is the crosstalk path.
- **RTD at the bottom of each loop** (low common-mode) — the reason the board exists.
- **Mixed-signal discipline (new):** the I²C bus and ADS1115 digital side are switching
  digital traffic next to µV-level analog. Partition analog/digital grounds with a single-
  point tie, keep I²C away from the R_ref taps and the sense pairs, decouple every ADS1115.
- Each ADS1115 sits **next to its two R_ref pairs**; route V_ref as a tight differential
  pair with the shortest possible path.
- 4-wire Kelvin preserved to each RTD; light sense-line RC filter at the T7 input.
- Test points on: each TOP node, each MID/Sense+ node, the rail, GND, SDA, SCL.

## Resolved inputs (locked 2026-06-22, Session 002 — Lucas; channel count revised
## 2026-07-09, Session 008 — Lucas: use the spare ADS1115 pair → 4 channels)
1. **RTD type = Pt100.** → T7 range **±0.1 V** (≈3–16 mV at ~100 µA, 100 K floor). Set a high resolution
   index and adequate mux settling per channel. (Does not affect R_ref sizing, which keys off
   the ADS range, or the CRD.)
2. **Channel count = 4** of the 7 T7 differential pairs are RTDs (was 3; the second ADS1115's
   AIN2/AIN3 differential pair was spare, so CH4 costs no new ADC). This fixes the repeated
   hardware:
   - **4 CRD/R_ref unit cells** (4× CRD SEMITEC S-101T, 4× R_ref 1.00 kΩ on the ADS ±0.256 V
     range).
   - **2 ADS1115** (1 chip per 2 channels → ceil(4/2) = 2): 4 differential V_ref reads, **4
     used, 0 spare**. Strap ADDR for **0x48 and 0x49**. U1 reads CH1/CH2; U2 reads CH3/CH4.
   - **4 RTD 4-wire connectors**; 4 of the 7 Sense± pairs go to the T7 analog (CB37). The
     other 3 T7 pairs remain free for non-RTD use.
   - **T7 analog connector = 2×5 header** (was 2×4): pins 1–6 = CH1–CH3 Sense± pairs,
     pins 7/8 = AGND (kept per the analog-reference intent), pins 9/10 = CH4 Sense±.

Cross-cal + ratiometric absorb component values, so these set ranges and counts, not
precision. The build is intentionally scalable: adding channels later means more unit cells
and (every 2 channels) another ADS1115 — no architectural change.
