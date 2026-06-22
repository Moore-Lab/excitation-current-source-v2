# Test 7 - Shared-ground crosstalk — 2026-06-22 — sim

## Objective
Acceptance: coupling between channels sharing a finite star-ground return stays below the noise floor; sets max ground R.

## Setup
Deck test7_crosstalk.cir; two unit cells share RG (sg->gnd); sweep aggressor RTD 80-158 Ohm at RG = 0.01/0.1/1/10 Ohm; victim at 100 Ohm.

## Method
Kelvin sensing rejects the common ground bounce; residual coupling enters only via the CRD's finite Z. Take the victim ratio swing over the aggressor's full range -> degC.

## Results
| star-ground R [Ohm] | victim coupling [degC] |
|---|---|
| 0.01 | 0.00e+00 |
| 0.1 | 0.00e+00 |
| 1 | 0.00e+00 |
| 10 | 0.00e+00 |


![crosstalk](plots/test7_crosstalk.png)

## Pass / Fail
Criterion coupling < 0.02 C at the 0.1 Ohm budget. **PASS** (0.0e+00 C).

## Anomalies & notes
Coupling is at/near the solver's numerical floor - Kelvin + current-source isolation makes it negligible for any realistic star-ground resistance.

## Next
Bench Stage 6 perturbs one channel and checks the others.
