# Test 4 - R_ref sizing / no-clip vs ADS1115 range — 2026-06-22 — sim

## Objective
Acceptance: worst-case V_ref stays under the ADS1115 +/-0.256 V range with margin and good effective bits.

## Setup
Deck test4_rref_sizing.cir; R_ref=820 Ohm; sweep CRD scale kc 0.7-1.3.

## Method
V_ref = drop across R_ref (RTD-independent); evaluate at kc=1.20 (+20% CRD, J500 guaranteed band max) and compare to 95% of full scale.

## Results
| quantity | expected | measured | unit |
|---|---|---|---|
| V_ref at +20% CRD | < 243 | 237.1 | mV |
| fraction of ADS FS | < 95 | 92.6 | % |
| effective bits used | high | 14.9 | bits |

![sizing](plots/test4_sizing.png)

## Pass / Fail
Criterion V_ref(+20%) < 95% FS. **PASS** (93% FS).

## Next
If more headroom is wanted, use the +/-0.512 V range (halves resolution) or a 750 Ohm <=10ppm part when restocked.
