* ============================================================================
* knobs.inc - control knobs carried as node voltages (0-impedance sources)
*
* Encoding the sweep/perturbation variables as node voltages lets every deck
* drive them with `alter` inside a headless .control loop - no re-parse, fully
* reproducible. Behavioral models (Rref, adc_vrtd) read these as v(<knob>).
*
*   dt    [degC]     board temperature delta from the cross-cal point
*   tcref [ppm/degC] R_ref tempco
*   tcgr  [ppm/degC] relative ADC gain tempco (G_T7/G_ADS)
*   off   [V]        additive offset referred to the V_RTD measurement
*   kc    [-]        CRD current scale (1.0 nominal, 1.1 = +10 %)
*   kref  [-]        R_ref value scale (1.0 nominal, 1.1 = +10 %)
*   rrtd  [Ohm]      RTD resistance (sweep with `.dc Vrrtd ...` for the RTD range)
* ============================================================================
Vdt    dt    0  DC 0
Vtcref tcref 0  DC 0
Vtcgr  tcgr  0  DC 0
Voff   off   0  DC 0
Vkc    kc    0  DC 1
Vkref  kref  0  DC 1
Vrrtd  rrtd  0  DC {RTD_0}
