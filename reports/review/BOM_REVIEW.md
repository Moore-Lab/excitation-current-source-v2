# BOM Review & Digi-Key Ordering List — rev-G (adds enclosure + panel-mount connectors)

> **rev-G (2026-07-13).** Board resized to **100 × 159.5 mm** for a Hammond 1455N extruded
> enclosure (slide-in slots, machinable end panels; see `docs/PANELS_AND_PINOUTS.md`).
> Connector changes vs rev-F, all live-verified on DigiKey with adversarial fact-checks:
>
> | Item | Part | DigiKey | Qty/board | Note |
> |---|---|---|---|---|
> | Enclosure | Hammond **1455N1601** (clear; BK = 1455N1601BK) | HM979-ND, $34.37, 308 pcs | 1 | end panels machined per `reports/review/panel-*.dxf` |
> | RTD inputs J1–J3,J7 | Phoenix **PT 1,5/5-3,5-H** (1984646) | 277-1723-ND | 4 | 3.5 mm push-in, 26–16 AWG; **pin 5 = cable shield** |
> | T7 analog J4 | Amphenol **RJHSE-5380** shielded RA RJ45 | 664-RJHSE5380-ND, $1.72, 14.8k | 1 | T568 map + shield policy in PANELS_AND_PINOUTS |
> | T7 I²C J5 | Molex KK 254 header **22-05-7048** | WM2786-ND | 1 | + housing **22-01-3047** (WM2002-ND) + 4× crimp **0008500160** (WM16517-ND); ⚠ pin order reversed — see PANELS_AND_PINOUTS |
> | Power J6 | Phoenix **PT 1,5/2-3,5-H** (1984617) | 277-1721-ND | 1 | |
> | Cables | CAT6a S/FTP patch (cut one end) + ferrules 26–20 AWG | any | — | |
>
> Superseded rev-F rows: MKDSN blocks (1729144/1729128), Sullins headers (S2012EC-05-ND /
> S1012EC-04-ND) — **do not order those**. Everything below (semiconductors + passives)
> is unchanged from rev-F and still current.

# Superseded header (rev-F) — passives/semis below remain the order list

Source: `hardware/*.kicad_sch` (rev-F) → `fab/bom/bom_fab.csv`.
Counts cross-checked against `docs/board_spec.md` for a **Pt100, 4-channel** board.

> **rev-F (2026-07-11).** Cryostat/stability respin on top of rev-E: the Pt100s sit **in
> vacuum down to ~100 K**, so excitation dropped to ~100 µA (~6× less self-heating), and
> the measurement path got precision-grade passives (C0G caps, 2 ppm reference, 0.1 %
> thin-film filters). Every line re-verified against **live Digi-Key product pages**
> with independent adversarial fact-checks. Prior lists: rev-E/rev-D in git history.

## Order list (Digi-Key) — quantities are per board

| Ref | Qty | Value | Footprint | MPN | Mfr | Digi-Key P/N | Status |
|-----|----|-------|-----------|-----|-----|--------------|--------|
| D1–D4 | 4 | CRD ~100 µA (band 0.05–0.21 mA), 100 V | D_SEMITEC_S-101T (SMD flat) | S-101T | SEMITEC | 4316-S-101TCT-ND | ✅ verified — 3,261 in stock, $2.31; see Finding 1 |
| R1–R3,R6 | 4 | 1.00 kΩ R_ref, **±0.05 %, ±2 ppm/°C** | R_1206 | TNPU12061K00AWEN00 | Vishay Dale | *(cut tape; confirm code at cart)* | ✅ verified — 3,105 in stock, $6.40; see Finding 2 |
| R4,R5 | 2 | 4.7 kΩ 1 % (I²C pull-ups) | R_0805 | RC0805FR-074K7L | Yageo | 311-4.70KCRCT-ND | ✅ verified — 433k in stock |
| R7–R14 | 8 | 1.00 kΩ **0.1 %, ±25 ppm/°C** (sense filter) | R_0805 | RG2012P-102-B-T5 | Susumu | RG20P1.0KBCT-ND | ✅ verified — 81,145 in stock, $0.068; order all from one strip (matching) |
| U1,U2 | 2 | ADS1115 16-bit ADC | MSOP-10 (no belly pad) | ADS1115IDGSR | TI | 296-38849-1-ND | ✅ verified — 46k in stock, $4.02 @ 10 |
| C1,C2 | 2 | 0.1 µF 50 V X7R 0805 (VDD decoupling) | C_0805 | CL21B104KBCNNNC | Samsung | 1276-1003-1-ND | ✅ verified — 7.67M in stock |
| C5–C8 | 4 | 0.1 µF 50 V **C0G/NP0** 1206 (sense filter) | C_1206 | GRM31C5C1H104JA01L | Murata | 490-6505-1-ND | ✅ verified — 40k in stock, $0.30; see Finding 3 |
| C3,C4 | 2 | 10 µF 25 V X5R 0805 (bulk) | C_0805 | CL21A106KACLRNC | Samsung | 1276-2397-1-ND | ✅ verified — 71k in stock; allocation squeeze, order promptly |
| J1–J3,J7 | 4 | RTD 4-wire terminal | MKDS(N) 1,5/4-5,08 | 1729144 | Phoenix | 277-1249-ND | ⚠ **only 131 in stock — order first** |
| J4 | 1 | T7 analog header | 2×5 2.54 mm vert. | PREC005DAAN-RC | Sullins | S2012EC-05-ND | ✅ 2×5 verified — 670 in stock; discontinued-at-DK (alt: Würth 61301021121 / 732-2672-ND) |
| J5 | 1 | T7 I²C header | 1×4 2.54 mm vert. | PREC004SAAN-RC | Sullins | S1012EC-04-ND | ✅ verified — 1,847 in stock; discontinued-at-DK |
| J6 | 1 | Power terminal | MKDS(N) 1,5/2-5,08 | 1729128 | Phoenix | 277-1247-ND | ✅ verified — 27.7k in stock |
| TP1–TP12 | 12 | Test pads | TestPoint_Pad | — copper feature, **do not order** | — | — | n/a |

**Legend:** ✅ verified on a live Digi-Key product page 2026-07-11 (stock/prices drift — re-check
at cart) · ⚠ see note.

**Count check vs board_spec (4-channel):** CRD D=4, R_ref=4, pull-ups=2, ADS=2, decouple=2,
bulk=2, RTD conns=4, headers J4/J5, power J6, TP=12, sense filters 8R+4C → **all pass; 47 parts.**

**Suggested order quantities for 3 assembled boards** (+10 % rounded up on small passives):
S-101T×14 (they're SMD-small and cheap insurance), R_ref×14, 4.7k×7, filter-1k×27 (one strip),
ADS1115×6 (+1 spare suggested — 0.5 mm pitch), 0.1 µF X7R×7, C0G×14, 10 µF×7, 4-pos blocks×12,
2-pos×3, 2×5×3, 1×4×3.

## Findings (must read before ordering)

**Finding 1 — CRD is now SEMITEC S-101T (rev-F design change).** Excitation lowered
0.24 → 0.10 mA nominal because the Pt100s are **in vacuum at ~100 K** — self-heating cannot
convect away; at 100 µA the sensor dissipates 0.3–1.6 µW (~6× less than rev-E). The S-101T
is a flat 2-lead SMD (easier hand assembly than the rev-E TO-92). Its band is huge
(0.05–0.21 mA, −50 %/+110 %) and its Ip tempco reaches +2.1 %/°C — **both are cancelled by
the ratiometric readout** (the design premise); SPICE test2 proves invariance across the
full band. Custom footprint from SEMITEC's recommended land pattern; **polarity: the
cathode is the hatched-band end of the marked face → toward pad 1** (silk bar + "K");
see `docs/datasheets/components.md`. Verify each part on arrival (~0.10 mA A→K above ~2 V).

**Finding 2 — R_ref upgraded to ±2 ppm/°C (stability-first).** With the current lowered,
R_ref re-sized to 1.00 kΩ (V_ref ≈ 100 mV nominal, ≤ 210 mV = 82 % FS at band max — never
clips, generous margin). The adversarial verify pass found **Vishay TNPU12061K00AWEN00**
(±0.05 %, **±2 ppm/°C**) in stock — at 2 ppm the reference is *no longer the drift limiter*
(ADC gain tempco and offset drift now set the budget; that is the success condition of the
stability priority, and SPICE test3's criterion was re-gated accordingly). Budget
alternatives, all verified in stock: TNPU12061K00AZEN00 (±5 ppm, $3.38, 4,040 pcs),
Susumu RG3216N-1001-W-T1 (±10 ppm, ±0.05 %, $0.96, 3,149 pcs), Panasonic ERA-8ARB102V
(±10 ppm, ±0.1 %, $0.92, 12,076 pcs). Bulk-metal-foil 1206 (Vishay VSMP/Y-series) is
exiting distribution — all 1 kΩ codes obsolete/0-stock at Digi-Key.

**Finding 3 — Sense-path passives now precision grade (rev-F policy).** C5–C8 are
**C0G/NP0** (Class-1: no DC-bias or temperature capacitance drift, no piezo, negligible
dielectric absorption) — 0.1 µF C0G 50 V exists in 1206 and is genuinely stocked (Murata
40k, TDK C3216C0G1H104J160AA 55k as backup at 445-7694-1-ND). The 1206 body no longer fits
across the J4 pin pairs, so **C5–C8 moved just east of J4** (back side, short B.Cu stubs) —
J4 assembly order is no longer constrained. R7–R14 upgraded to 0.1 %/±25 ppm thin film;
matching matters more than absolute TCR (series with high-Z inputs) — use one cut-tape
strip. **Deliberately NOT C0G/precision:** C1,C2 (rail decoupling) and C3,C4 (bulk) stay
X7R/X5R — they are not in the measurement path, and 10 µF does not exist in C0G; I²C
pull-ups R4,R5 stay generic (digital).

**Finding 4 — carried from rev-E, still true:** 1729144 (4-pos Phoenix) had only 131 pcs —
order first. Sullins headers are last-time-buy at Digi-Key (stock ample for this build).
Never order 490-3283-1-ND (maps to a 2.7 nF part, not the 0.1 µF). The 10 µF/25 V/0805
class is in an allocation squeeze.

**Finding 5 — cryo range note (host/bench, not BOM):** the Pt100 window now extends to
~30 Ω at 100 K. The host R→T conversion must use the Callendar–Van Dusen low-temperature
branch (or a calibration table) below 0 °C — flagged for the bench/host phase.

Sources (live Digi-Key product pages + manufacturer datasheets, fetched 2026-07-11):
SEMITEC S-101T (DK id 16579005; CRD catalog P22-23-CRD.pdf incl. land pattern p.23),
Vishay TNPU12061K00AWEN00/AZEN00 (tnpue3.pdf), Murata GRM31C5C1H104JA01L (id 2548139),
TDK C3216C0G1H104J160AA (id 2733129), Susumu RG2012P-102-B-T5 (id 1240655) and
RG3216N-1001-W-T1, Panasonic ERA-8ARB102V (id 5141062), plus rev-E verifications
(ADS1115, Yageo, Samsung, Phoenix, Sullins).
