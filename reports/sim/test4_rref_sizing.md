# Test 4 - R_ref sizing / no-clip vs ADS1115 range — 2026-06-22 — sim

## Objective
Acceptance: worst-case V_ref stays under the ADS1115 +/-0.256 V range with margin and good effective bits.

## Setup
Deck test4_rref_sizing.cir; R_ref=1.00 kOhm; sweep CRD scale kc 0.4-2.2.

## Method
V_ref = drop across R_ref (RTD-independent); evaluate at kc=2.10 (0.21 mA, S-101T guaranteed band max) and compare to 90% of full scale.

## Results
| quantity | expected | measured | unit |
|---|---|---|---|
| V_ref at band-max CRD (0.21 mA) | < 230 | 211.0 | mV |
| fraction of ADS FS | < 90 | 82.4 | % |
| effective bits used | high | 14.7 | bits |

![sizing](plots/test4_sizing.png)

## Pass / Fail
Criterion V_ref(band max) < 90% FS. **PASS** (82% FS).

## Next
Headroom is generous at 82% FS worst case; a low-band S-101T (0.05 mA) reads V_ref at ~20% FS - averaging covers the resolution loss.
