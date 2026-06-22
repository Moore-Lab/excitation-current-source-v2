* ============================================================================
* params.inc - shared design parameters for the RTD-readout SPICE harness
* Track B (SPICE). Source of truth: docs/board_spec.md (Pt100, 3 channels).
*
* Every value here is a *design nominal*; the harness exists to prove the
* result is INVARIANT to most of them (cross-cal + ratiometric absorb them).
* Anything a deck sweeps/perturbs it does with `alter` on a top-level knob
* source (see knobs in each deck), not by editing this file.
* ============================================================================

* ---- CRD (current-regulator diode, 1N5283 / CDLL5283) ----------------------
* Nominal ~0.22 mA, +/-10 %. Exact value is irrelevant (measured live), but it
* must be stable & quiet over one scan. Z_CRD is the finite dynamic impedance
* of the low-current part (MOhm-range) - the realism that makes compliance and
* crosstalk non-ideal. Both are intentionally sweepable.
.param I_CRD0 = 220u      $ CRD nominal current [A]
.param Z_CRD  = 5Meg      $ CRD dynamic (slope) impedance [Ohm], assumption - swept
.param VL_CRD = 1.05      $ CRD limiting voltage for regulation [V] (1N5283-class)

* ---- Reference resistor R_ref ----------------------------------------------
* Sized to the ADS1115 range, NOT the RTD. 910 Ohm -> V_ref ~200 mV nominal,
* ~220 mV at +10 % CRD, inside ADS1115 +/-0.256 V. Absolute value absorbed by
* cross-cal; only tempco/stability matter (<=10 ppm/degC).
.param R_REF0  = 910      $ R_ref nominal [Ohm]
.param TC_RREF = 10       $ R_ref tempco budget [ppm/degC] (datasheet target)

* ---- The two ADCs (gain terms) ---------------------------------------------
* Only the RATIO G_T7/G_ADS and its tempco matter. We carry both as 1.0 and put
* the entire relative-gain tempco on the T7 path (equivalent, since the ratio is
* what the measurement uses). Units are dimensionless V/V.
.param G_T7_0  = 1.0      $ T7 path gain (V_RTD measurement)
.param G_ADS_0 = 1.0      $ ADS1115 path gain (V_ref measurement)
.param TC_GR   = 10       $ relative ADC gain tempco budget [ppm/degC]

* ---- Supply ----------------------------------------------------------------
.param VRAIL_NOM = 5.0    $ nominal rail [V]
.param VRAIL_MIN = 4.5    $ worst-case low rail [V] (10 % sag) for compliance

* ---- Pt100 RTD sweep window (board_spec: ~18-35 mV at ~220 uA) -------------
* Pt100, IEC 60751: R(T) = 100*(1 + 3.9083e-3 T - 5.775e-7 T^2)  (T in degC)
*   -50 degC -> 80.31 Ohm , 0 degC -> 100 Ohm , +150 degC -> 157.33 Ohm
.param RTD_MIN = 80.31     $ Ohm  (~ -50 degC)
.param RTD_0   = 100.0     $ Ohm  (0 degC)
.param RTD_MID = 138.51    $ Ohm  (+100 degC)
.param RTD_MAX = 157.33    $ Ohm  (~ +150 degC)
* Local Pt100 sensitivity dR/dT near 0 degC = 0.39083 Ohm/degC. A fractional
* ratio error f maps to dT ~= f * R / (dR/dT) ~= 256 * f  degC near 0 degC.
.param PT100_DRDT = 0.39083  $ Ohm/degC at 0 degC
