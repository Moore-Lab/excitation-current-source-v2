# Test 1 - DC operating point & CRD compliance — 2026-06-22 — sim

## Objective
Acceptance (a): the CRD keeps regulating (V across it > V_L) across the full Pt100 sweep at the worst-case low rail.

## Setup
Deck sim/netlists/test1_dc_compliance.cir; ngspice op sweep of Vrrtd 80-158 Ohm at rail = 5.0 V and 4.5 V; CRD = 240 uA || 4 MOhm.

## Method
Vcrd = v(rail)-v(top) over the sweep; take the minimum at the low rail and compare to V_L.

## Results
| quantity | expected | measured | unit |
|---|---|---|---|
| min V across CRD (rail 4.5 V) | > 1.2 | 4.264 | V |
| margin above V_L | > 0 | 3.064 | V |
| V_RTD span (Pt100) | 18-35 | 19.3-38.1 | mV |

![compliance](plots/test1_compliance.png)

## Pass / Fail
Criterion min Vcrd > V_L=1.2 V. **PASS** (margin 3.06 V).

## Next
Re-point at the exported KiCad netlist in Wave 3.
