# BOM Review & Digi-Key Ordering List — rev-D (4-channel RTD readout, sense filters fitted)

Source: `hardware/*.kicad_sch` (rev-C) → `fab/bom/bom_fab.csv`.
Counts cross-checked against `docs/board_spec.md` for a **Pt100, 4-channel** board.

## Order list (Digi-Key)

| Ref | Qty | Value | Footprint | MPN | Mfr | Digi-Key P/N | Status |
|-----|----|-------|-----------|-----|-----|--------------|--------|
| D1–D4 | 4 | CRD ~220 µA | D_MELF (DO-213AB) | CDLL5283/TR | Microchip | 150-CDLL5283/TR-ND | ✅ confirmed |
| R1–R3,R6 | 4 | 910 Ω R_ref | R_1206 | **TNPU1206 910 Ω 0.1% ≤10 ppm** | Vishay | *parametric — select code* | ⚠ **see Finding 1** |
| R4,R5 | 2 | 4.7 kΩ 1% | R_0805 | RC0805FR-074K7L | Yageo | 311-4.70KCRCT-ND | ◑ confirm at cart |
| R7–R14 | 8 | 1 kΩ 1% (sense filter) | R_0805 | RC0805FR-071KL | Yageo | 311-1.00KCRCT-ND | ◑ confirm at cart |
| U1,U2 | 2 | ADS1115 16-bit ADC | MSOP-10 (VSSOP) | ADS1115IDGSR | TI | 296-38849-1-ND | ✅ confirmed |
| C1,C2 | 2 | 0.1 µF 50 V X7R | C_0603 | GRM188R71H104KA93D | Murata | 490-3283-1-ND | ◑ confirm at cart |
| C5–C8 | 4 | 0.1 µF 50 V X7R (sense filter, back side) | C_0603 | GRM188R71H104KA93D | Murata | same as C1,C2 | ◑ confirm at cart |
| C3,C4 | 2 | 10 µF 25 V X5R | C_0603 | GRM188R61E106KA73D | Murata | *MPN confirmed; DK P/N confirm* | ◑ confirm at cart |
| J1–J3,J7 | 4 | RTD 4-wire terminal | MKDS 1,5/4-5,08 | **1729144** | Phoenix | 277-1249-ND | ⚠ **corrected — Finding 2** |
| J4 | 1 | T7 analog header | 2×5 2.54 mm | PREC005DAAN-RC (2×5 vert.) | Sullins | *confirm 2×5 vertical code* | ◑ confirm at cart |
| J5 | 1 | T7 I²C header | 1×4 2.54 mm | PREC004SAAN-RC | Sullins | 2774850 / S2211EC-04-ND | ✅ confirmed |
| J6 | 1 | Power terminal | MKDS 1,5/2-5,08 | 1729128 | Phoenix | 277-1247-ND | ✅ confirmed |
| TP1–TP12 | 12 | Test pads | TestPoint_Pad | — copper feature, **do not order** | — | — | n/a |

**Legend:** ✅ MPN + Digi-Key P/N verified from a Digi-Key product page · ◑ MPN is a correct
standard part; verify exact Digi-Key P/N + live stock at cart · ⚠ see finding below.

**Count check vs board_spec (4-channel):** CRD D=4, R_ref=4 (R1–R3,R6), pull-ups R4,R5=2, ADS U=2
(ceil(4/2)), decouple C1,C2=2, bulk C3,C4=2, RTD conns=4 (J1–J3,J7), headers J4/J5, power J6,
TP=12, sense filters 8R+4C → **all pass; 47 parts.** (rev-C: CH4 added on U2's spare AIN2/3; J4 grew to 2×5 —
pins 1–6 = CH1–CH3 Sense±, 7/8 = AGND, 9/10 = CH4 Sense±.)

## Findings (must read before ordering)

**Finding 1 — R_ref tempco: original part failed the binding spec.** The previous MPN
(Susumu RG3216P-911-B-T5) is **±25 ppm/°C**, but `board_spec.md` §R_ref requires **≤10 ppm/°C**
(binding). Cross-cal absorbs R_ref's *absolute value*, so tolerance is irrelevant — but its
**drift between recalibrations** is one of the three accuracy limiters, and 25 ppm ≈ doubles
that term vs 10 ppm. Recommended: a **0.1 %, ≤10 ppm/°C, 910 Ω, 1206** thin-film part —
**Vishay TNPU1206** family (or Panasonic/Susumu equivalents). Pick the exact 910 Ω order code
on Digi-Key's parametric filter (tolerance ≤0.1 %, TCR ≤10 ppm, 1206, in stock). *This is the
one part where getting the spec right matters most; I did not pin an exact order code rather
than assert an unverified one.*

**Finding 2 — RTD connector part number was wrong (now corrected).** The prior MPN **1729160
is the 6-position** MKDS; J1–J3 use the **4-position** footprint. Corrected to **1729144**
(MKDS 1,5/4-5,08, DK 277-1249-ND). J6's 1729128 (2-pos) was already correct.

**Finding 3 — Generic-passive/​header Digi-Key P/Ns marked ◑ "confirm at cart":** the MPNs are
correct standard parts, but live stock/pricing and the exact 2×4 header order code (J4) should
be confirmed in the cart. This is normal procurement hygiene, not a design gap.

**Finding 4 — RESOLVED (rev-D).** The sense-line RC filter is now fitted: R7–R14 (1 kΩ) +
C5–C8 (0.1 µF differential at J4, mounted on the **back side** across the pin pairs — hand
assembly, no courtyard). SPICE test5 now describes the real hardware.

Sources (Digi-Key product pages): [CDLL5283](https://www.digikey.com/en/products/detail/microchip-technology/1N5283/7607015),
[ADS1115IDGSR](https://www.digikey.com/en/products/detail/texas-instruments/ADS1115IDGSR/2231567),
[Phoenix 1729144](https://www.digikey.com/en/products/detail/phoenix-contact/1729144/260617),
[Phoenix 1729128](https://www.digikey.com/en/products/detail/phoenix-contact/1729128/260615),
[Sullins PREC004SAAN-RC](https://www.digikey.com/en/products/detail/sullins-connector-solutions/PREC004SAAN-RC/2774850),
[Murata 10 µF GRM188R61E106KA73D](https://www.digikey.com/en/products/detail/murata-electronics/GRM188R61E106KA73D/9867922),
[Vishay TNPU high-precision thin-film](https://www.digikey.com/en/product-highlight/v/vishay-dale/tnpu-high-precision-thin-film-resistor).
