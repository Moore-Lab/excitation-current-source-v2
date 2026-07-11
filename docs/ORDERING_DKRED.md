# Ordering — DigiKey DKRed (PCB) + BOM Manager (parts) + stencil

Everything here was verified against live DigiKey pages / TechForum staff posts on
**2026-07-11** (multi-agent research with independent adversarial fact-checks; details in
the session transcripts). Stock, pricing and policies drift — re-check at cart time.
Parts list + order quantities: [`../reports/review/BOM_REVIEW.md`](../reports/review/BOM_REVIEW.md) (rev-F).

## 1. DKRed fab — capabilities vs this board

| DKRed (fixed spec) | This board (rev-F) |
|---|---|
| 2 or 4 copper layers | 4 layers ✓ |
| 0.5″×0.5″ min – 10″×10″ max | 122 × 104 mm (4.81″ × 4.10″) ✓ |
| min trace/space 5 mil | min clearance 0.13 mm ≈ 5.1 mil ✓ |
| min drill 8 mil | min via drill 0.3 mm ≈ 11.8 mil ✓ |
| no internal cutouts | none ✓ |
| FR4 TG170–180, 0.062″, 1 oz, ENIG, red mask/white silk (fixed) | fine — no impedance control needed on this board; ENIG helps hand soldering |

Minimum **4 copies**; "starting at $1.50/in²" is the 2-layer anchor (4-layer priced only in
the live quote; ~19.7 in² board). Built in 5–10 business days, free US shipping, fabbed at
a California board house (per DigiKey staff posts).

## 2. Gerber/drill export (KiCad 10) — exact settings

Upload a **Gerber ZIP, not the native `.kicad_pcb`** — PCB Builder accepts KiCad-native
files but KiCad ≥ 9 uploads have a staff-confirmed parsing bug with failures still reported
as of Mar 2026.

`File → Plot…` (Gerber): layers **F.Cu, In1.Cu, In2.Cu, B.Cu, F.Paste, F.Mask, B.Mask,
F.Silkscreen, B.Silkscreen, Edge.Cuts** (B.Paste unnecessary — the only back-side parts,
C5–C8, are hand-soldered). Options: ✓ extended X2, ✓ subtract mask from silk, ✓ Protel
extensions, ✗ "Use drill/place file origin" (= absolute). Do **not** include
Courtyard/Fab/User layers in the zip.

*Generate Drill Files…*: Excellon, **millimeters, decimal, absolute origin**, and
**UNCHECK "PTH and NPTH in single file"** — DKRed's KiCad requirements list separate
`-PTH.drl`/`-NPTH.drl`, and their FAQ auto-rejects submissions with missing/empty drill
data. (The NPTH file holds only the 4 mounting holes — include it.)

One flat zip (no subfolders). Note: `scripts/fab_drop` produces X2 gerbers + a **merged**
drill file — for DKRed either add `--excellon-separate-th` to its drill line or use the
GUI settings above, and exclude the extra layers when zipping.

## 3. Stencil

DigiKey **does not sell stencils** ("Stencils are not available at this time" — live PCB
Builder FAQ). Order from a US stencil vendor (e.g. OSH Stencils) using the same zip; they
cut from `*-F_Paste.gtp`. A 4-mil (0.1 mm) frameless stainless foil suits 0805/1206 +
MSOP-10. Skip a B-side stencil.

## 4. BOM upload (DigiKey myLists / BOM Manager)

Accepts .csv/.xlsx/.xls; needs at least a part-number column (DigiKey P/N **or** MPN) plus
Quantity. Auto-mapped headers include *DigiKey Part Number* (takes precedence — use it,
every line in BOM_REVIEW has a verified one), *Manufacturer Part Number*, *Quantity*,
*Reference Designator*, *Customer Reference*, *Description*; you confirm per-column mapping
on upload. Export CSV from Google Sheets rather than Excel (Excel can mangle numeric part
numbers to scientific notation and prepend a UTF-8 BOM).

## 5. Order sequence + gotchas (as of 2026-07-11)

1. **Phoenix 1729144 first** — only 131 pcs in stock (need 12 for 3 boards).
2. 10 µF/25 V/0805 X5R class is in an allocation squeeze — CL21A106KACLRNC promptly.
3. S-101T (CRD): buy spares for binning (3,261 in stock, modest).
4. Sullins headers are last-time-buy at DigiKey (stock ample; Würth 61301021121 is the
   active-status 2×5 alternative).
5. Never order 490-3283-1-ND (it is a 2.7 nF part, not the 0.1 µF — stale P/N from rev-B).
6. Sense-filter resistors R7–R14: one cut-tape strip (same lot) for matching.
