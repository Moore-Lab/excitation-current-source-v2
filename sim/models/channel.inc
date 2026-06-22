* ============================================================================
* channel.inc - one RTD readout unit cell (CRD + R_ref + RTD + both ADCs)
*
* Assumes the including deck has already defined:
*   - node `rail`  (driven by a Vrail source)
*   - the knob nodes from knobs.inc (dt, tcref, tcgr, off, kc, kref)
* and has .include'd params.inc, crd.inc, meas.inc.
*
* Nodes exposed: top (R_ref top / V_ref+), mid (R_ref bottom = RTD top = V_ref- =
* V_RTD sense+), nref (ADS reading), nrtd (T7 reading). RTD sense pair is taken
* across the RTD body (mid..0), so it is independent of force-lead resistance.
*
* Current loop: rail -> CRD -> top -> R_ref -> mid -> RTD -> 0 -> Vrail -> rail.
* ============================================================================

Xcrd  rail top  kc  crd                                            $ current source
Rref  top  mid  R = 'R_REF0 * v(kref) * (1 + v(tcref)*1e-6*v(dt))' $ V_ref = I*Rref
Rrtd  mid  0    R = 'v(rrtd)'                                      $ RTD: .dc-sweep Vrrtd

Xref  top mid  nref               adc_vref            $ ADS1115 reads V_ref = (top-mid)
Xrtd  mid 0    nrtd  dt tcgr off  adc_vrtd            $ T7 reads V_RTD = (mid-0)
