* ============================================================================
* crd.inc - current-regulator-diode model (1N5283 / CDLL5283)
*
* Modeled as an ideal current source in parallel with the part's finite dynamic
* impedance Z_CRD (the low-current 1N528x parts sit high, MOhm-range). The
* current value is scaled by knob node v(kc) so a deck can perturb it +/-10 %
* (kc=1.1) to prove the result is invariant. Uses globals I_CRD0, Z_CRD.
*
* Pinout / polarity (matches board_spec signal chain): anode -> +rail,
* cathode -> R_ref top. Node np = anode side (rail), nm = cathode side (top).
* Conventional current flows np -> nm externally (out of the cathode into R_ref).
*
*   .subckt crd np nm kc
* ============================================================================
.subckt crd np nm kc
* Independent-source convention: positive current flows np->nm *inside* the
* source, i.e. it is delivered out of nm into the external circuit. That drives
* I down through R_ref -> RTD -> ground, returning to np. Exactly the loop we want.
Bi   np nm  I = 'I_CRD0 * v(kc)'
* Finite dynamic impedance: adds v(np,nm)/Z_CRD of voltage-dependent current.
* This is the term that makes compliance and ground-bounce crosstalk non-ideal.
Rz   np nm  {Z_CRD}
.ends crd
