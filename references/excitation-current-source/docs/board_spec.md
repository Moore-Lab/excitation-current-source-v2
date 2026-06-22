# Multi-Channel 4-Wire RTD Readout — REF200 + LabJack T7 Pro

Ratiometric, current-source-per-RTD board to replace the series-chain topology. Each
RTD gets its own loop near ground (kills the CMRR / position-dependent noise), and each
channel measures its own excitation against a precision reference resistor so the
REF200's absolute accuracy and drift drop out of the result.

Measurement equation (per channel):

    R_RTD = R_ref · (V_RTD / V_ref)

Both voltages carry the **same** current, so the current value never enters the answer.

---

## 1. Unit cell

One REF200 current-source section, one reference resistor, one RTD. RTD sits at the
bottom of the stack (lowest common-mode → smallest CMRR error).

```
        +V rail (LDO, +5 V)
            │
        ┌───┴────┐
        │ REF200 │   source "High" terminal(s)
        │ source │
        └───┬────┘   source "Low" terminal(s)
            │  ← I (200 µA or 100 µA), set by strap
        TOP ●─────────────► AIN (V_ref +)        ── measure V_ref across R_ref
            │
          [R_ref]   precision, 0.01%, ≤10 ppm/°C
            │
        MID ●─────────────► AIN (V_ref − / shared with RTD Sense+)
            │  Force+  (long lead to RTD)
            ▼
        ┌───────┐
        │  RTD  │   Sense+ ●──────► AIN (V_RTD +)   ── Kelvin, no force-lead drop
        │ 4-wire│   Sense− ●──────► AIN (V_RTD −)
        └───┬───┘
            │  Force−  (long lead)
            ▼
          STAR GND
```

- **Reference resistor on top, RTD on the bottom.** Keeps the RTD differential
  common-mode at ≈ V_RTD/2 (tens of mV), so the T7's finite CMRR contributes
  negligibly — the failure mode of the old series chain.
- **R_ref is on-board (2-wire is fine)** — short traces, known value. The RTD keeps
  full 4-wire Kelvin.
- **Substrate (pin 6) → GND** (most negative node) for rated DC performance. Leave the
  unused current-mirror section (pins 3/4/5) open.

---

## 2. REF200 pinout & strap (SOIC-8, top view)

| Pin | Name           | Function                         |
|----:|----------------|----------------------------------|
| 1   | I1 Low         | Source 1, low (output) terminal  |
| 2   | I2 Low         | Source 2, low (output) terminal  |
| 3   | Mirror Common  | unused                           |
| 4   | Mirror Output  | unused                           |
| 5   | Mirror Input   | unused                           |
| 6   | Substrate      | tie to GND (most negative)       |
| 7   | I2 High        | Source 2, high (supply) terminal |
| 8   | I1 High        | Source 1, high (supply) terminal |

Current enters "High", exits "Low" into the load. One chip = **two 100 µA sections**.

**Mode A — 200 µA, one channel/chip** (parallel both sources, per datasheet Fig. 19a):
- Pin 8 + Pin 7 → +V rail
- Pin 1 + Pin 2 → TOP node (into R_ref)

**Mode B — 100 µA, two channels/chip** (sources independent):
- Channel A: Pin 8 → +V rail, Pin 1 → R_ref_A → RTD_A
- Channel B: Pin 7 → +V rail, Pin 2 → R_ref_B → RTD_B

Optional reverse-V protection (only matters on fault/hot-plug): one 1N4148 in parallel
with each source per datasheet Fig. 17a; clamps reverse to ~0.7 V. Not needed in normal
operation since the Low node always sits below the High node.

---

## 3. Current & reference-resistor selection

| RTD    | Current | Mode | V_RTD (−50…+150 °C) | R_ref  | V_ref  | T7 range | Chips |
|--------|---------|------|---------------------|--------|--------|----------|-------|
| Pt100  | 200 µA  | A    | 16 – 31 mV          | 100 Ω  | 20 mV  | ±0.1 V   | 1/ch  |
| Pt1000 | 100 µA  | B    | 80 – 157 mV         | 1 kΩ   | 100 mV | ±1 V     | ½/ch  |
| Pt1000 | 200 µA  | A    | 160 – 314 mV        | 1 kΩ   | 200 mV | ±1 V     | 1/ch  |

Rule of thumb: **R_ref = RTD nominal (R0)** → ratio ≈ 1, balanced resolution on both
measurements.

- **Pt100 → run at 200 µA.** At 100 µA the 10 mV signal fights the T7 resolution floor.
- **Pt1000 → run at 100 µA.** Plenty of signal, and you get **two channels per chip**,
  halving chip count and cost.

Reference resistor is now your dominant accuracy/drift term, so spend here (this is the
budget the old plan wasted on a buck regulator): 0.01 %, ≤10 ppm/°C thin-film or foil.
Self-heating is negligible (4 nW in a 100 Ω at 200 µA), so any package is fine — but keep
it out of airflow/thermal gradients and away from anything that dissipates heat.

---

## 4. Power

- **Single +5 V rail from a low-noise LDO** (e.g. LT3045 if you want it quiet; honestly
  any clean LDO works because ratiometric rejects rail-induced current variation). Feed
  it from whatever you already have. **No DC-DC buck** — it only adds switching trash next
  to a µV-level measurement.
- Compliance check: source sees Vrail − (V_ref + V_RTD) ≈ 5 V − ~0.05–0.3 V ≈ 4.7–4.95 V,
  well above the 2.5 V minimum. 3.3 V would also work.
- REF200 source noise is a non-issue here: ~1 nA p-p (0.1–10 Hz) → ~140 nV p-p across a
  100 Ω, and the slow part cancels ratiometrically anyway. The measurement noise floor
  stays set by the T7 ADC and Johnson noise, not the excitation.

---

## 5. T7 AIN budget — the channel-count decision

The T7 has **14 AIN → 7 differential pairs**. How many RTDs you can read depends on the
measurement mode:

| Mode | Per channel | Kelvin? | Max channels | When to use |
|------|-------------|---------|--------------|-------------|
| **Full differential** | V_RTD diff pair + V_ref diff pair = 4 AIN | full 4-wire | **3** | ≤3 RTDs, best noise |
| **Single-ended subtract** | TOP_Rref, Sense+, Sense− as 3 SE reads | full 4-wire | **4** | 4 RTDs; CM is sub-volt so SE is fine |
| **Calibrated current** | V_RTD diff pair only = 2 AIN | full 4-wire | **7** | many RTDs; drop per-channel V_ref |

- **Full differential** is cleanest but caps at 3 channels.
- **Single-ended subtract**: read TOP-of-R_ref, Sense+, and Sense− each vs GND and
  subtract in software. Because every node is < 1 V, SE accuracy is fine and you keep
  Kelvin (you're still reading the actual sense leads). 3 AIN/channel → 4 channels.
- **Calibrated current**: measure each channel's actual current once with a good DMM,
  store it, and trust the REF200's 25 ppm/°C drift + long-term stability. Drops V_ref,
  so 2 AIN/channel → up to 7. Trade ratiometric robustness for density. Reasonable if the
  board's temperature is stable to a few °C.

If you need more than 7, the current sources are independent — add a second T7, or
multiplex sense pairs through an external low-leakage mux (watch settling).

**Read raw voltages and compute R in software** — don't use the AIN_EF RTD feature here,
since that assumes the single internal source. Just grab V_RTD and V_ref and apply the
ratio.

---

## 6. Layout & wiring

- **Star ground:** all RTD Force− returns, LDO ground, and T7 GND meet at one point.
  Independent loops near ground are the whole reason the noise goes away — don't let them
  share a long return trace.
- **Force vs Sense:** route as separate pairs all the way to the RTD; Kelvin connection
  made at the RTD terminals. Sense leads carry only the **T7 input bias current ≈ 20 nA**
  (datasheet — *not* pA-level as earlier assumed), so the force-lead IR drop never appears
  in V_RTD, and the bias current itself drops a negligible µV across normal lead resistance.
- **Sense pairs:** twisted/shielded; add a light differential RC at the T7 input
  (≈0.1 µF across the pair) for the EMI rejection the old setup lacked. **Size the series R
  carefully:** 20 nA bias × 1 kΩ = **20 µV** per line — common-mode (cancels) only if the
  two series Rs match well; mismatch is a *differential* error sitting in the signal budget.
  Prefer a smaller series R (e.g. 100–200 Ω, matched) or explicitly budget the drop. Keep
  source impedance ≤ the T7's 1 kΩ max.
- **Mux settling — RC must be per-channel, before the mux (Track B deck 05).** A single
  shared 0.1 µF after the mux needs ~1.7 ms to settle vs a ~1 ms dwell; a per-channel RC
  ahead of the mux never re-settles between hops. Set the T7 AIN settling / resolution index
  so each channel fully settles within its dwell — this was the second noise suspect, so
  don't reintroduce it by scanning too fast.
- **R_ref placement:** tight to the chip, short traces, thermally quiet.

---

## 7. Per-channel BOM (Pt100, 200 µA example)

| Item | Qty | ~Cost (1-off) | Notes |
|------|----:|---------------|-------|
| REF200AU (SOIC-8) | 1 | ~$12–18 | 1 ch @200 µA, or 2 ch @100 µA — verify distributor stock |
| Reference resistor 100 Ω 0.01 % ≤10 ppm/°C | 1 | ~$2–8 | accuracy-limiting part |
| 1N4148 (optional reverse protection) | 1 | ~$0.05 | per source |
| Sense RC filter (R + cap) | 1 set | ~$0.50 | EMI/anti-alias |
| **Shared:** LDO + caps | — | ~$2–5 | one per board |
| **Shared:** enclosure, connectors | — | per old BOM | screw terminals fine |

For Pt1000 @ 100 µA the chip cost roughly halves per channel (two channels share one
REF200). Net: comfortably under the original ~$50/channel target, and the money goes into
the reference resistor where it actually buys accuracy.

---

## Resolved configuration (was: open inputs)

The two gating inputs are now decided (Lucas, 2026-06-19):

1. **RTD type → Pt100.**
2. **Channel count → 3.**

Derived design point:

| Parameter | Value | Source |
|-----------|-------|--------|
| Excitation current | **200 µA** per channel | §3 (Pt100 rule of thumb); offset-margin (see note) |
| REF200 strap mode | **Mode A** (both sources paralleled, §2 Fig. 19a) | follows 200 µA |
| Chips | **3× REF200** (1 per channel; no spare) | Mode A = 1 ch/chip |
| Reference resistor | **R_ref = 100 Ω**, ≤10 ppm/°C (Track A part: VSMP1206, 0.2 ppm/°C, 0.02 %) | rule of thumb R_ref = R0; ratio ≈ 1 (§3) |
| V_ref (across R_ref) | **20 mV** | 200 µA × 100 Ω |
| V_RTD (−50…+150 °C) | **16 – 31 mV** | 200 µA × (80…157 Ω) |
| Measurement mode | **Full differential**, 4-wire Kelvin | §5; 3 ch ⇒ 12 of 14 AIN |
| T7 AIN range | **±0.1 V** (V_RTD max 31 mV > ±0.01 V range) | §5 |

> **Current = 200 µA, decided 2026-06-22 from the SPICE budget + the verified T7 spec.**
> Started at 100 µA (chip density: 2 chips/3 ch); Track B's accuracy deck then showed the
> budget is **ADC-offset-limited, not R_ref-limited**, because ratiometric cancels gain and
> source current but **not** the ADC's input offset. The LabJack T7-Pro ±0.1 V range spec
> (verified): **absolute accuracy ±20 µV** (offset+gain+linearity; offset not broken out),
> noise **<1 µV p-p / 22-bit eff.**, tempco **15 ppm/°C**, input bias **20 nA**. Offset on a
> 10 mV (100 µA) signal is ~0.2 % → ~520 m°C **unnulled**. **200 µA doubles V_ref/V_RTD to
> 20/16–31 mV, halving the offset-referred error** (1 µV residual → ~13 m°C vs ~26 m°C at
> 100 µA) for one extra REF200 per channel; self-heating still negligible (4 µW in R_ref).
>
> **Mandatory regardless of current:** **per-channel ADC offset nulling** (e.g. interleaved
> zero/short reads) + averaging — without it neither current meets ±100 m°C. With nulling,
> 200 µA gives comfortable margin (~30 m°C); residual is offset *drift* (≈1.5 µV/°C if the
> 15 ppm/°C is of-FS) + averaged noise, so keep the board thermally quiet and re-null
> periodically. (Recorded in SESSION_LOG Session 003; supersedes the Session-001 100 µA choice.)
