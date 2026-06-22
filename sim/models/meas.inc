* ============================================================================
* meas.inc - the two ADC measurement paths as differential gain blocks
*
* The whole point of the architecture: V_RTD and V_ref are digitized by
* DIFFERENT converters (T7 vs ADS1115), so the raw ratio carries G_T7/G_ADS.
* Each is modeled as a high-impedance differential gain block (a B-source reading
* node voltages draws no current -> Kelvin sensing is preserved automatically).
*
* FINITE CMRR: each reads its differential input PLUS a fraction 1/cmrr of its
* common-mode (referred to the converter's own ground = node 0). This is the term
* that lets shared-return ground bounce couple into a reading (Test 7). `cmrr` is
* a linear ratio passed per instance; it DEFAULTS to 1e12 (effectively infinite),
* so every other deck is numerically unaffected. Test 7 passes finite values.
*
* Knob nodes injected per deck:
*   dt    - board temperature delta from cross-cal [degC]
*   tcgr  - relative gain tempco [ppm/degC]  (entire G_T7/G_ADS drift lives here)
*   off   - additive offset referred to the V_RTD measurement [V]
* Uses globals G_T7_0, G_ADS_0.
* ============================================================================

* ---- V_ref path: ADS1115 reading across R_ref (top - mid) ------------------
* No tempco/offset here; by convention the entire *relative* gain tempco is
* carried on the T7 path (only the ratio matters).
.subckt adc_vref p m out  params: cmrr=1e12
Bvr  out 0  V = 'G_ADS_0 * ( (v(p)-v(m)) + 0.5*(v(p)+v(m))/cmrr )'
.ends adc_vref

* ---- V_RTD path: T7 Pro reading the RTD Kelvin pair (sp - sn) --------------
* out = G_T7_0*(1 + tcgr*1e-6*dt)*[ (sp-sn) + 0.5*(sp+sn)/cmrr ] + off
* The (sp-sn) tap is the 4-wire SENSE pair, distinct from the force nodes, so
* force-lead resistance never enters the reading.
.subckt adc_vrtd sp sn out dt tcgr off  params: cmrr=1e12
Bvt  out 0  V = 'G_T7_0 * (1 + v(tcgr)*1e-6*v(dt)) * ( (v(sp)-v(sn)) + 0.5*(v(sp)+v(sn))/cmrr ) + v(off)'
.ends adc_vrtd