* ============================================================================
* meas.inc - the two ADC measurement paths as ideal gain blocks
*
* The whole point of the architecture: V_RTD and V_ref are digitized by
* DIFFERENT converters (T7 vs ADS1115), so the raw ratio carries G_T7/G_ADS.
* We model each as a high-impedance differential gain block (a B-source reading
* node voltages draws no current -> Kelvin sensing is preserved automatically).
*
* Knob nodes injected per deck:
*   dt    - board temperature delta from cross-cal point [degC]
*   tcgr  - relative gain tempco [ppm/degC]  (entire G_T7/G_ADS drift lives here)
*   off   - additive offset referred to the V_RTD measurement [V]
* Uses globals G_T7_0, G_ADS_0.
* ============================================================================

* ---- V_ref path: ADS1115 reading across R_ref (top - mid) ------------------
* No tempco/offset here; by convention the entire *relative* gain tempco is
* carried on the T7 path (only the ratio matters). out = G_ADS_0*(top-mid).
.subckt adc_vref p m out
Bvr  out 0  V = 'G_ADS_0 * (v(p) - v(m))'
.ends adc_vref

* ---- V_RTD path: T7 Pro reading the RTD Kelvin pair (sp - sn) --------------
* out = G_T7_0*(1 + tcgr*1e-6*dt)*(sp-sn) + off
* The (sp-sn) tap is the 4-wire SENSE pair, distinct from the force nodes, so
* force-lead resistance never enters the reading.
.subckt adc_vrtd sp sn out dt tcgr off
Bvt  out 0  V = 'G_T7_0 * (1 + v(tcgr)*1e-6*v(dt)) * (v(sp) - v(sn)) + v(off)'
.ends adc_vrtd
