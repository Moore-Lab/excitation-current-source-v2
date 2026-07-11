# Test 3 - Monte-Carlo accuracy -> degC error — 2026-06-22 — sim

## Objective
Acceptance (c): over board dT the accuracy stays within target, with the reference resistor NOT the limiting term (rev-F: 2 ppm/C R_ref; ADC gain tempco + offset drift set the residual).

## Setup
Deck test3_montecarlo.cir; N=2000 Gaussian samples; dT=10 C; sigmas R_ref/gain=2/10 ppm/C, offset=1 uV; cross-cal C verified = R_ref0 = 1000 Ohm.

## Method
Per sample: cross-cal at dt=0, then op at dt with sampled tempco/offset; fractional error -> Pt100 degC via x255.9.

## Results
| term | 1-sigma input | degC (1-sigma) |
|---|---|---|
| R_ref tempco | 2 ppm/C | 0.0051 |
| relative ADC gain tempco | 10 ppm/C | 0.0256 |
| V_RTD offset drift | 1 uV | 0.0256 |
| **analytic RSS** | | **0.0365** |
| **MC sigma (sim)** | | **0.0365** |
| MC 95th pct \|err\| | | 0.0710 |

![hist](plots/test3_mc_hist.png)

## Pass / Fail
Criterion sigma <= 0.05 C AND R_ref tempco not limiting. **PASS** (sigma=0.0365 C; R_ref term 0.0051 C <= gain 0.0256 / offset 0.0256 C).

## Anomalies & notes
Offset term scales as 1/V_RTD (~10 mV at 100 uA) and is now, with ADC gain tempco, the accuracy limiter between recals - the deliberate rev-F trade for ~6x lower cryostat self-heating. Mitigations: recal cadence, thermal stability of the T7, and tracking the T7 internal-GND channel for offset drift.

## Next
Inject real part tempco/offset specs; bench Stage 7 measures C drift.
