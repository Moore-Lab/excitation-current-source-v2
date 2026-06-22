# SPICE model strategy

Track-B model layer for the REF200 RTD board. Source of truth for *what the decks
believe the hardware is*. Re-point at the real KiCad-exported netlist at Wave 3
(see `sim/README.md` and `docs/sessions/trackB.md`).

## REF200 — `ref200.lib`

**No vendor model exists.** TI's REF200 product page ships a datasheet but **no
SPICE/PSpice model** (checked 2026-06-19). If TI ever publishes one, drop it here and
have `02_ratiometric` / `06_noise` `.include` it instead of `ref200.lib` — the rest of
the harness is unaffected because every deck references the section only through the
`ref200_src` subckt name.

Until then, each 100 µA section is modelled per `TESTING_PLAN.md`:

| Element | Value | Justification |
|---------|-------|---------------|
| Ideal DC current source | `iset` (100 µA resolved) | the section's defining behaviour |
| Parallel output resistance `rout` | 50 MΩ | datasheet output impedance 20–100 MΩ; 50 MΩ nominal |

Mode A (200 µA) = two sections in parallel → just instantiate `ref200_src` twice
across the same nodes, or set `iset=200u` and `rout=25meg`.

The finite `rout` is deliberately included so the ratiometric decks can *prove* the
result is independent of it: the same series current flows through `R_ref` and the
RTD regardless of how much `rout` shunts, so the ratio `V_RTD/V_ref` is exact.

## RTD — swept resistor

The RTD is a plain resistor swept across its operating band. Resistance ↔ temperature
uses Callendar–Van Dusen (IEC 60751) in `sim/scripts/rtd.py`, **not** a SPICE element,
because the decks only need the resistance and the *temperature* mapping belongs in
the analysis (it converts a resistance error into an equivalent °C error).

- Pt100: ~80.3 Ω (−50 °C) … 157.3 Ω (+150 °C)
- Pt1000: ~803 Ω … 1573 Ω

## R_ref — parameter

`r_ref` is a parameter (`config.py`), 100 Ω resolved. Tolerance (0.01 %) and tempco
(10 ppm/°C) are applied in the Monte-Carlo accuracy analysis, not baked into the deck,
so one deck serves nominal, corner, and statistical runs.

## Noise

An ideal current source is **noiseless** in ngspice `.noise`, so `06_noise.cir`
computes only what ngspice models natively and correctly: the **Johnson noise of
`R_ref`, the RTD, and the sense RC-filter resistors, band-limited by the filter**,
output-referred to the ADC differential input.

The **REF200 excitation current noise** is then added analytically by
`analysis.py` from the datasheet figures, because it is not a SPICE-native element:

- White: **20 pA/√Hz** → ×`R` gives the excitation voltage-noise density.
- Flicker (0.1–10 Hz): **1 nA p-p** → ≈ `1n/6.6` ≈ 0.15 nA rms over the decade band.

Both are tiny (20 pA × 100 Ω = 2 nV/√Hz white) and the slow/flicker part cancels
ratiometrically anyway, but they are carried explicitly so the budget is complete and
honest rather than silently dropping the excitation term.