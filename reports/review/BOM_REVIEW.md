# BOM Review & Digi-Key Ordering List — rev-E (4-channel RTD readout, DFM/availability respin)

Source: `hardware/*.kicad_sch` (rev-E) → `fab/bom/bom_fab.csv`.
Counts cross-checked against `docs/board_spec.md` for a **Pt100, 4-channel** board.

> **rev-E (2026-07-11).** Every line below was re-verified against **live Digi-Key product
> pages** (13 research agents + independent adversarial fact-checks). Drivers: (a) the CRD
> and both Murata MLCCs went unbuyable; (b) hand-assembly DFM — no MELF, no 0603, 0805+
> only; (c) R_ref re-sized for the new CRD's wider band. Prior list: see git history (rev-D).

## Order list (Digi-Key) — quantities are per board

| Ref | Qty | Value | Footprint | MPN | Mfr | Digi-Key P/N | Status |
|-----|----|-------|-----------|-----|-----|--------------|--------|
| D1–D4 | 4 | CRD ~240 µA, 50 V | TO-92-2_CRD-J500 (THT) | J500 TO-92 2L | Linear Integrated Systems | 4004-J500TO-922L-ND | ✅ verified — 793 in stock, $6.24 @ 10 |
| R1–R3,R6 | 4 | 820 Ω R_ref, 0.1 %, ≤10 ppm/°C | R_1206 | RN73H2BTTD8200B10 | KOA Speer | 2019-RN73H2BTTD8200B10CT-ND | ✅ verified — 2,612 in stock; see Finding 2 |
| R4,R5 | 2 | 4.7 kΩ 1 % | R_0805 | RC0805FR-074K7L | Yageo | 311-4.70KCRCT-ND | ✅ verified — 433k in stock |
| R7–R14 | 8 | 1 kΩ 1 % (sense filter) | R_0805 | RC0805FR-071KL | Yageo | 311-1.00KCRCT-ND | ⚠ **0 stock, 17-wk lead — see Finding 4** |
| U1,U2 | 2 | ADS1115 16-bit ADC | MSOP-10 (VSSOP, no belly pad) | ADS1115IDGSR | TI | 296-38849-1-ND | ✅ verified — 46k in stock, $4.02 @ 10 |
| C1,C2,C5–C8 | 6 | 0.1 µF 50 V X7R **0805** | C_0805 | CL21B104KBCNNNC | Samsung | 1276-1003-1-ND | ✅ verified — 7.67M in stock, $0.022 @ 25 |
| C3,C4 | 2 | 10 µF 25 V X5R **0805** | C_0805 | CL21A106KACLRNC | Samsung | 1276-2397-1-ND | ✅ verified — 71k in stock; see Finding 5 |
| J1–J3,J7 | 4 | RTD 4-wire terminal | MKDS(N) 1,5/4-5,08 | 1729144 | Phoenix | 277-1249-ND | ⚠ **only 131 in stock — order promptly**; Finding 6 |
| J4 | 1 | T7 analog header | 2×5 2.54 mm vert. | PREC005DAAN-RC | Sullins | **S2012EC-05-ND** | ✅ verified 2×5 — 670 in stock; discontinued-at-DK (last-time-buy); Finding 7 |
| J5 | 1 | T7 I²C header | 1×4 2.54 mm vert. | PREC004SAAN-RC | Sullins | **S1012EC-04-ND** | ✅ verified — 1,847 in stock; prior P/N was wrong, Finding 7 |
| J6 | 1 | Power terminal | MKDS(N) 1,5/2-5,08 | 1729128 | Phoenix | 277-1247-ND | ✅ verified — 27.7k in stock |
| TP1–TP12 | 12 | Test pads | TestPoint_Pad | — copper feature, **do not order** | — | — | n/a |

**Legend:** ✅ verified on a live Digi-Key product page 2026-07-11 (stock/prices drift — re-check
at cart) · ⚠ see finding.

**Count check vs board_spec (4-channel):** CRD D=4, R_ref=4 (R1–R3,R6), pull-ups R4,R5=2, ADS U=2
(ceil(4/2)), decouple C1,C2=2, bulk C3,C4=2, RTD conns=4 (J1–J3,J7), headers J4/J5, power J6,
TP=12, sense filters 8R+4C → **all pass; 47 parts.**

**Suggested order quantities for 3 assembled boards** (+10 % rounded up on small passives):
D×12, R_ref×14, 4.7k×7, 1k×27, ADS1115×6 (consider +1 spare — 0.5 mm pitch hand soldering),
0.1 µF×20, 10 µF×7, 4-pos blocks×12, 2-pos×3, 2×5 header×3, 1×4 header×3.

## Findings (must read before ordering)

**Finding 1 — CRD replaced: CDLL5283 → LIS J500 TO-92 2L (rev-E design change).** The
CDLL5283/TR MELF is Active but has **zero stock** at Digi-Key — factory order only (MOQ
145–280 pcs, ~$5.50/ea, 40-week lead); the THT sibling 1N5283 is $19/ea at a 100-pc MOQ,
25-week lead. An exhaustive sweep (SEMITEC, Central, LIS, MCC, Diotec) confirmed **no
flat-SMD CRD with 180–270 µA nominal is stocked at Digi-Key**. The J500 (0.24 mA nominal,
0.192–0.288 mA band, 50 V, TO-92) is the verified in-stock equivalent and is far friendlier
to hand assembly than MELF. Footprint changed to a project-local mirrored TO-92-2 — see
`docs/datasheets/components.md` §CRD for the **polarity note (silent-fatal)**.

**Finding 2 — R_ref re-sized 910 Ω → 820 Ω (consequence of Finding 1).** The J500 band is
±20 % (vs ±10 % for the 1N5283), so 910 Ω would hit 0.288 mA × 910 Ω = 262 mV — **clipping
the ADS1115 ±0.256 V range**. Per board_spec §R_ref's own sizing rule: 820 Ω → 197 mV
nominal, ≤236 mV (92 % FS) at the guaranteed band max. **Every qualifying 750 Ω part
(KOA/Susumu/Vishay/Bourns, ≤0.1 %, ≤10 ppm) is zero-stock**; RN73H2BTTD8200B10 (820 Ω,
±0.1 %, ±10 ppm/°C) was the *only* in-stock spec-compliant part in the 715–820 Ω window —
adversarially verified against the KOA datasheet code decode. SPICE test4 re-gated at the
band max: 93 % FS, PASS.

**Finding 3 — Murata MLCCs unbuyable; old 0.1 µF Digi-Key P/N was wrong.**
GRM188R71H104KA93D (0.1 µF 0603) is **obsolete** at Digi-Key, and the previously listed
P/N 490-3283-1-ND actually maps to a *different part* (GRM1885C1H272JA01D, 2.7 nF C0G) —
**never order it**. GRM188R61E106KA73D (10 µF 0603) is Active but 0 stock (17-wk). rev-E
moved all caps to **0805** for hand assembly (DFM rule: nothing smaller than 0805) with the
Samsung parts above — exact spec matches, verified in stock.

**Finding 4 — 1 kΩ 0805: design MPN backordered.** RC0805FR-071KL is Active but 0 stock
(17-week lead). It is a jellybean: order Digi-Key's suggested equivalent **RC0805FR-071KP**
(~18k shown in stock; exact cut-tape code unconfirmed — confirm at cart) or any in-stock
1 kΩ 1 % 0805.

**Finding 5 — 10 µF/25 V/0805 is in an allocation squeeze.** Four major-brand equivalents
(Samsung -YNNNE, Murata ×2, TDK, Yageo) are all backordered; CL21A106KACLRNC (71k) and
Taiyo Yuden TMK212BBJ106MGHT (6.9k, backup, DK 587-6440-1-ND) were the in-stock options.
Order promptly.

**Finding 6 — Phoenix blocks: low stock on the 4-pos; series naming.** 277-1249-ND had only
**131 in stock** (need 12 for 3 boards) — order first. Note Digi-Key/Phoenix list 1729144/
1729128 under the **MKDSN** 1,5 naming (successor to MKDS 1,5; same 5.08 mm pitch) — the
KiCad MKDS footprint fit should be (and was, rev-B) low-risk, but glance at the MKDSN
drawing before ordering.

**Finding 7 — Sullins headers: corrected P/N + discontinued status.** The prior J5 P/N
S2211EC-04-ND was **wrong** (that code family is dual-row → a 2×4); the correct 1×4 code is
**S1012EC-04-ND**. J4's PREC005DAAN-RC is confirmed 2×5 (10-pos, 2-row) = **S2012EC-05-ND**.
Both are "Discontinued at Digi-Key" — remaining stock (1,847 / 670) is plenty for this
build; the active-status 2×5 alternative is Würth 61301021121 (DK 732-2672-ND, 10.9k).

**Finding 8 — carried from rev-D, still true:** sense-filter caps C5–C8 mount on the
**back side** across J4's pin pairs (hand assembly; solder them **before** inserting J4).
Now 0805, courtyard/silk-less instances, same scheme as rev-D's 0603s.

Sources (live Digi-Key product pages, fetched 2026-07-11): J500 `4004-J500TO-922L-ND`
(id 13688168), KOA `RN73H2BTTD8200B10` (id 10105100), Samsung `CL21B104KBCNNNC` (id 3886661)
and `CL21A106KACLRNC` (id 3890483), TI `ADS1115IDGSR` (id 2231567), Yageo `RC0805FR-074K7L`,
Phoenix `1729144` (id 260617) / `1729128` (id 260615), Sullins `S1012EC-04-ND` /
`S2012EC-05-ND` (id 2774889); LIS J500 datasheet doc 201126 Rev A10; KOA RN73H datasheet.
