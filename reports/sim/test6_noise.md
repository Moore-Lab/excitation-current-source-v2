# Test 6 - Noise of the ratio — 2026-06-22 — sim

## Objective
Acceptance (d): ratio noise below the per-channel resolution target, with the CRD current-noise risk explicitly bounded.

## Setup
ngspice .noise -> Johnson PSD (V_ref 3.69, V_RTD 1.29 nV/rtHz); BW=10 Hz. T7=1 uV and ADS=5 uV RMS are ASSUMPTIONS (named in run_all.py) - the bench must confirm them.

## Method
RSS-combine each path's noise, divide by its signal (V_ref=201 mV, V_RTD=22.1 mV), RSS the two fractions, x255.9 -> degC. Only the Johnson terms are physically derived (and negligible); the ADCs dominate, so the PASS is CONDITIONAL on the assumed ADC noise. We therefore back-solve the max-allowable T7 noise. CRD noise is common to both reads -> CANCELS in the ratio under simultaneous sampling; its bound is the i_n that would reach target if sampling were NOT simultaneous.

## Results
| source | contribution [degC RMS] | note |
|---|---|---|
| Johnson R_ref (ngspice) | 0.0148 m | physical |
| Johnson RTD (ngspice) | 0.0471 m | physical |
| ADS1115 V_ref | 6.3648 m | **assumed 5 uV** |
| T7 V_RTD | 11.5776 m | **assumed 1 uV** |
| **total** | **13.212 m** | vs 20 m target |
| **max-allowable T7 noise** | | **1.64 uV RMS** (back-solved) |
| CRD current-noise bound (worst case) | | 2.90 nA/rtHz |

![noise](plots/test6_noise.png)

## Pass / Fail
Conditional criterion: total < 20 mdegC **iff** T7 <= 1.64 uV and ADS <= 5 uV RMS. At the assumed 1/5 uV: **PASS** (13.2 mdegC, 1.5x margin). CRD bound 2.9 nA/rtHz worst-case (~0 if simultaneous).

## Anomalies & notes
PASS rides on assumed ADC noise; the physically-derived (Johnson) terms are ~0.05 mdegC. The number the bench (Track C, Wave 3 Stage 5) must beat: **T7 <= 1.64 uV RMS** (at ADS 5 uV, BW 10 Hz). The small V_RTD (~22 mV) is why the T7 path dominates.

## Next
Bench Stage 5 (noise/position) measures real T7/ADS noise; Stage 8 the CRD.
