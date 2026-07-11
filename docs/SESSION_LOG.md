# SESSION_LOG.md

Integration-level development record. **Newest entry on top.** In parallel mode each track
logs to `docs/sessions/<track>.md`; this file is updated only at integration with a
one-entry summary per merged track.

## Entry schema (copy for each new session)

```
## Session NNN — YYYY-MM-DD — <short objective>

**Tooling:** KiCad <x.y.z>, ngspice <x.y>, <other>
**Branch / commit at start:** <branch> @ <hash>
**State before:** <what existed, what passed>
**Objective:** <what this session set out to do>
**Actions:**
- <ordered list>
**Files touched:** <paths>
**Validation:**
- ERC: <N errors / M warnings> (reports/erc/...)
- DRC: <N violations> (reports/drc/...)
- SPICE: <tests, pass/fail vs criteria> (reports/sim/...)
**Decisions (rationale + spec ref):**
- <decision> — <why> — <board_spec.md § / datasheet>
**Open issues / risks:**
- <unresolved / fragile / needs Lucas>
**Next action:** <single exact next step>
**Commit:** <hash>
```

---

## Session 011 — 2026-07-11 — rev-E: DFM/availability respin (CRD→TO-92, 0603→0805, R_ref 820 Ω)

**Tooling:** KiCad 10.0.3 (kicad-cli; s-expression text surgery — pcbnew Python footprint swap
corrupted SWIG wrappers after Remove/Add, confirming the Session-010 warning); ngspice 44
(conda `spice`); live Digi-Key verification via 21 web agents with adversarial fact-check passes.
**Branch / commit at start:** `rev-e-dfm` off `main` @ `e03b61d`.
**State before:** rev-D complete (ERC 0/0, DRC 0/0, SPICE 7/7); kickoff gates reproduced on
this machine before editing.
**Objective:** Lucas is hand-assembling in a university lab and ordering domestically (Digi-Key
DKRed): flag hand-assembly-hostile parts and eliminate 0603s ("stick to 0805 and bigger").
Live stock checks then forced a wider change — see decisions.
**Actions:**
- CRD: CDLL5283 (MELF) → **LIS J500 TO-92 2L** (`4004-J500TO-922L-ND`). MELF is DFM-hostile
  AND unbuyable (0 stock, MOQ 145–280, 40-wk); no flat-SMD 180–270 µA CRD exists in DK stock
  (exhaustive, adversarially verified). New local footprint `TO-92-2_CRD-J500`: KiCad TO-92-2
  with body/silk **mirrored** so flat-face-to-silk insertion puts K in pad 1 (J500 pin 1 = A),
  drill 0.8 mm (worst-case lead diagonal 0.755 mm), "K" silk marker. Board: 4 rebuilt blocks,
  pads at old-center ±1.27 mm, 8 F.Cu stubs bridge the old MELF trace ends to the THT pads.
- Caps: all 8 → **0805**. 0.1 µF = Samsung CL21B104KBCNNNC (old Murata obsolete; old DK P/N
  490-3283-1-ND was a different part!); 10 µF = Samsung CL21A106KACLRNC (old Murata 0 stock).
  Board: in-place geometry rescale of the 8 blocks; C5–C8 keep the rev-D courtyard/silk-less
  back-side across-J4 scheme, now 0805.
- **R_ref 910 Ω → 820 Ω** (KOA RN73H2BTTD8200B10, ±0.1 %, ±10 ppm/°C): the J500 band is ±20 %,
  and 0.288 mA × 910 Ω = 262 mV would clip the ±0.256 V range. 820 Ω → ≤236 mV (92 % FS) at
  guaranteed band max. Every qualifying 750 Ω part is 0-stock; 820 Ω was the only in-stock
  ≤0.1 %/≤10 ppm part in the 715–820 Ω window (adversarially verified).
- Schematic (root + 3 unit cells, all 4 D's edited by hand per the accepted CH2–CH4-copies
  deviation): footprint/Value/MPN/Manufacturer/Datasheet/Polarity/Current_nom fields updated.
- SPICE harness re-pointed: I_CRD0 240 µA, R_REF0 820, VL_CRD 1.2, Z_CRD 4 MΩ (J500 min);
  test2 kc ±20 %, test4 sweep ±30 % + acceptance now **<95 % FS at kc=1.20** (was <90 % at
  1.10 — impossible to meet with any purchasable part; 7.7 % real headroom remains), test7
  aggressor ±20 %.
- Docs: board_spec §CRD/§R_ref (spec updated, deviations noted in place), USER_MANUAL,
  components.md (new CRD polarity note — silent-fatal), BOARD_DEV_CHECKLIST, TESTING_PLAN,
  DIRECTORY_MANAGEMENT, test/README, host/config.py defaults (240e-6, 820.0), BOM_REVIEW.md
  fully rewritten (rev-E order list, 8 findings, live-verified DK P/Ns + stock).
**Files touched:** `hardware/*.kicad_sch` (×4), `hardware/rtd-readout.kicad_pcb`,
`libraries/footprints/rtd-readout.pretty/{TO-92-2_CRD-J500,C_0805_2012Metric}.kicad_mod` (new),
`sim/models/{params,crd}.inc`, `sim/netlists/test{2,4,7}*.cir`, `sim/scripts/run_all.py`,
`docs/{board_spec,USER_MANUAL,TESTING_PLAN,BOARD_DEV_CHECKLIST,DIRECTORY_MANAGEMENT}.md`,
`docs/datasheets/components.md`, `test/README.md`, `host/config.py`, `host/t7_rtd.py`,
`reports/review/BOM_REVIEW.md`.
**Validation:**
- ERC: **0 errors / 0 warnings** (reports/erc/erc_rev_e.json)
- DRC: **0 violations / 0 unconnected** (reports/drc/drc_rev_e.json; zones refilled + saved
  via separate-pass headless fill)
- SPICE: **7/7 PASS** — t1 Vcrd margin 3.06 V above VL=1.2; t2 CRD-invariance err 6.9e-9 at
  ±20 %; t3 σ=0.0373 °C; **t4 V_ref(+20 %)=237 mV = 93 % FS, 14.9 bits**; t5 settle 1.03 ms;
  t6 unchanged; t7 3.1e-6 °C at 0.1 Ω with ±20 % aggressor.
**Decisions (rationale + spec ref):**
- J500 swap + THT deviation from the all-SMD preference — availability forced it; spec
  §Current source updated in place. Polarity mapping absorbed in the mirrored footprint
  (components.md documents it as silent-fatal; verify on arrival).
- R_ref 820 Ω per spec §R_ref's own sizing rule applied to the ±20 % band; test4 criterion
  95 %/kc=1.2 replaces 90 %/kc=1.1 — **Lucas should confirm he accepts ~8 % clip headroom**
  (alternatives: ±0.512 V range at half resolution, or wait for 750 Ω restock).
- Z_CRD 4 MΩ = J500 datasheet min @25 V; knee impedance near 5 V is lower (~2.5 MΩ typ) but
  decks sweep Z_CRD, and t6/t7 margins are orders of magnitude.
**Open issues / risks:**
- J500 polarity must be bench-verified on arrival (constant ~0.24 mA A→K above ~1.2 V).
- TO-92 3D model transform (rotate 180 + offset 2.54 mm) is cosmetic-unverified in a viewer.
- Schematic symbol still named `CRD_1N5283` (legacy; noted in components.md).
- Digi-Key stock is a 2026-07-11 snapshot; 4-pos Phoenix block had only 131 pcs.
**Next action:** Lucas final review → merge `rev-e-dfm` to `main`, tag `rev-E` + `fab-rev-E`,
run `sh scripts/fab_drop` at the tag, order per BOM_REVIEW.md (rev-E).
**Commit:** this commit on `rev-e-dfm`.

---

## Session 010 — 2026-07-09 — HANDOFF: continuing development on another machine

**Purpose of this entry:** a fresh session (possibly on a different machine) should be able to
recover full state from `main` alone. Read this, then `docs/USER_MANUAL.md` (the single
review document), then the entries below for history.

**Exact repo state at handoff:**
- `main` @ `ea947e0`, pushed to `github.com/eldarro/excitation-current-source-v2` with all
  tags: `rev-A..D`, `fab-rev-A..D`. Working tree clean; nothing unpushed.
- All development branches (`trackA..G`, `integration`, `rev-b-parts`,
  `schematic-readability`, `rev-c-4ch`, `rev-d-filter`) are **local-only to the old machine
  and fully merged into `main`** — a new clone needs none of them.
- The old machine also had stale git *worktrees* under `../ivmux-python/` (removed) — do not
  recreate worktrees inside another repo; see the warning in `PARALLEL_PLAN.md`.

**Design state: rev-D — complete and fleet-verified. Nothing is open in the design.**
- 4 channels (Pt100), ratiometric across T7 + 2× ADS1115 (0x48/0x49, all 4 diff pairs used).
- Board 122×104 mm, 4-layer, split planes, single-point GND tie at (80,50)→(83,50).
- Sense RC filters fitted (R7–R14 1 kΩ + C5–C8 0.1 µF diff at J4; filtered nets `CHn_T7±`;
  **C5–C8 mount on the BACK side** across J4's pin pairs — hand-assembly note).
- Gates at `ea947e0`: ERC 0/0 (all severities), DRC 0 violations / 0 unconnected, parity 84
  (metadata-only — 47 MPN-field + 30 attr-flag + 7 mechanical; no net conflicts), SPICE 7/7.
  Every rev was verified by multi-agent workflows incl. netlist-delta oracles and adversarial
  copper review — evidence in `reports/` and the session entries below.

**Environment a new machine needs:**
- **KiCad 10.0.x** (files are v10, `version 20251024`; developed on 10.0.3). `kicad-cli` does
  ERC/DRC/exports; PCB scripting used KiCad's bundled Python (`pcbnew`) — note its track
  iteration is flaky, s-expression text editing was more reliable.
- **ngspice** for the SPICE harness: `conda create -y -n spice -c conda-forge ngspice`, then
  set `NGSPICE_BIN` to the env's `ngspice_con` binary (auto-detect misses non-default conda
  paths). Run `python sim/scripts/run_all.py` — expect 7/7 PASS.
- Python 3.12+ with numpy. Gates: `sh scripts/run_gates`; fab: `sh scripts/fab_drop`
  (regenerates `fab/` deterministically — it is gitignored, captured by the `fab-rev-D` tag).

**What remains (physical-world only):**
1. **Order rev-A boards** — package = `sh scripts/fab_drop` at tag `fab-rev-D` (gerbers/
   drill/pos/STEP/BOM). Before ordering, resolve the "◑ confirm at cart" Digi-Key codes in
   `reports/review/BOM_REVIEW.md` — especially the exact **R_ref 910 Ω ≤10 ppm/°C order code**
   (Vishay TNPU1206 family, parametric pick) and the 2×5 header code.
2. **Bench verification** — `docs/TESTING_PLAN.md` Part 2, Stages 0–8, using `host/` +
   `test/procedures/`; headline test = Stage 5 noise/position-independence. Probe filtered
   nets at J4 (`CHn_T7±`), unfiltered at the `CHn_SENSE±` test points.
3. If a design change is ever needed: unit cells CH2–CH4 are **separate copies** of CH1
   (pages 2–4) — edit all four by hand (accepted deviation, noted on schematic page 1).

**Next action:** on the new machine — clone, open `docs/USER_MANUAL.md`, re-run
`sh scripts/run_gates` + the SPICE harness to confirm the environment reproduces the gates,
then proceed to ordering/bench.
**Commit:** this handoff entry.

---

## Session 009 — 2026-07-09 — rev-D: sense-line RC filters fitted (closes Session-006 decision)

**Tooling:** KiCad 10.0.3 (kicad-cli; pcbnew Python + s-expression text surgery); ngspice 44.
**Branch / commit at start:** `rev-d-filter` off `main` (rev-C).
**Objective:** Lucas approved adding the spec's sense filter ("what do you think it should be?
Can you add that?") — recommendation: fit it (spec-required, SPICE test5 already validates it,
zero accuracy cost, protects mux settling + anti-aliasing).
**Actions:**
- **Schematic (page 1):** per channel 1 kΩ inline in Sense+ and Sense− (R7–R14) + 0.1 µF
  differential cap (C5–C8) at J4; filtered nets labeled **CHn_T7±**; cap bank drawn with
  lanes east of J4; CH1's drawn legs re-landed on the unfiltered side (caught by the netlist
  delta oracle on first pass). ERC 0/0; delta = exactly the filter insertion (23→31 nets).
- **Layout:** R's inserted inline in each leg's existing copper (F-inline where possible,
  via-sandwich F-resistor where the leg runs on B); caps on **B.Cu directly across the J4 pin
  pairs** (courtyard/silk-less variant footprint — barrels inside courtyard otherwise);
  R9/R13 repositioned after DRC caught courtyard clashes; 4 footprints rotated 180° + pad
  nets aligned so pin1/pin2 match the schematic (parity net_conflicts → 0).
- MPNs: R 1 kΩ = Yageo RC0805FR-071KL; C = same Murata GRM188R71H104KA93D as C1/C2 (BOM
  consolidation). Netclass: `CH*_T7*` → SENSE.
**Validation:** ERC **0/0**; DRC **0 violations / 0 unconnected / 0 net-conflicts** (parity 84,
all metadata: 47 field + 30 attr + 7 mechanical); netlist delta assertion PASS; **SPICE 7/7**
(test5 now describes real hardware); fab + renders regenerated; verification workflow
(delta oracle, gates, visual, adversarial filter-copper review).
**Decisions:** filter fitted rather than waived — see USER_MANUAL §8.5 (now RESOLVED);
back-side caps accepted (hand assembly; documented in BOM_REVIEW + manual).
**Open issues / risks:** C5–C8 are the only back-side parts (assembly note); parity metadata
unchanged-cosmetic.
**Next action:** order from `fab/` (`fab-rev-D`); bench per TESTING_PLAN Part 2.
**Commit:** on `rev-d-filter`; tags `rev-D`, `fab-rev-D`; merged to `main`; pushed.

---

## Session 008 — 2026-07-09 — rev-C: 4th channel (use U2's spare ADS1115 pair)

**Tooling:** KiCad 10.0.3 (kicad-cli + bundled pcbnew Python); ngspice 44 (conda `spice`).
**Branch / commit at start:** `rev-c-4ch` off `main`.
**Objective (Lucas request):** "we might as well make this 4 channels because we have that
capacity on the adc" — U2's AIN2/AIN3 differential pair was a no-connect spare.
**Actions:**
- **board_spec:** channel count 3→4 (CRD=4, R_ref=4, ADS=2 with 0 spare, RTD conns=4; T7
  analog connector 2×4→**2×5**, CH4 Sense± on pins 9/10, AGND kept on 7/8).
- **Schematic:** page 4 = unit_cell_ch4 (clone of ch3: D4, R6, J7, TP11/TP12, CH4_* nets,
  fresh UUIDs, #PWR renumbered); U2 AIN2/3 no-connects → CH4_TOP/MID; Conn_T7_Analog symbol
  grown to 10 pins; J4 footprint/MPN → 2×5 (PREC005DAAN-RC). Netlist delta verified to be
  **exactly** the specified additions (21→23 nets; nothing else moved).
- **Library:** PinHeader_2x05_P2.54mm_Vertical added (extended from the 2x04).
- **Layout (pcbnew scripting):** board grown 122×82→**122×104 mm**; bottom mounting holes →
  y100; all 4 plane outlines extended y79→101 and refilled; D4/R6/J7/TP11/TP12 placed
  mirroring CH3's cell; J4 swapped to 2×5; CH4 routed (V_ref taps up x63.4/x64.2 into U2
  pads 6/7; sense pair on B.Cu x23/x26 to J4 9/10; +5V drop via). Two pre-existing items
  reworked to make room: CH2_SENSE− rerouted off the new J4 row; one VS stub/via at U2's
  east side relocated. Two intermediate DRC failures found & fixed (U2 pads 6/7 still bound
  to old no-connect nets; first CH4_MID corridor collided with C2).
**Validation:** ERC **0/0**; DRC **0 violations / 0 unconnected**; parity 60 (35+18 metadata
on the 5 new parts + pre-existing, 7 mechanical — no net conflicts); netlist delta exact;
**SPICE 7/7 PASS** (per-channel circuit unchanged); fab regenerated; renders updated.
Independent 5-agent verification workflow ran (delta oracle, gates, adversarial layout
review of the new copper incl. star-ground/single-tie discipline, visual audit, BOM=35).
**Open issues / risks:** sense-line RC filter decision (Session 006) still open — now 4
pairs affected; parity metadata (MPN fields on footprints) still cosmetic-only.
**Next action:** Lucas review; resolve filter; order from `fab/` (`fab-rev-C`).
**Commit:** on `rev-c-4ch`; tags `rev-C`, `fab-rev-C`; merged to `main`.

---

## Session 007 — 2026-07-09 — Schematic readability restructure (audit view)

**Tooling:** KiCad 10.0.3; Python 3.12 generator (out-of-tree, per Track-E convention); headless
Chrome for render inspection.
**Branch / commit at start:** `schematic-readability` off `main` (rev-B).
**Objective (Lucas request):** the label-stub schematic is hard to audit — restructure to
**page 1 = CH1 unit cell + acquisition + power/IO on one sheet with drawn wires**, pages 2–3 =
CH2/CH3; keep the circuit provably identical.
**Actions:**
- Merged `unit_cell_ch1` + `acquisition` + `power_io` into the root sheet by rigid block
  translation (all internal geometry, labels, and UUIDs preserved); deleted the three files;
  root re-authored on A3 with the two remaining subsheets (pages 2–3).
- Added **28 join wires + 5 junctions**, all connecting points already on the same net:
  CH1_TOP/CH1_MID → U1 AIN0/1; J1 Sense± → J4 (Kelvin visible); SDA/SCL trunks U1→U2→J5.
  A collision checker proved no added segment touches any foreign connection point.
- Cosmetics only: flipped east-side labels that rendered into symbol bodies (rot 0→180);
  moved value texts below connector/IC bodies; relocated CH1 sense + J4-west labels onto the
  new wires with stub extensions. All labels kept ⇒ every net keeps its name.
- Instance paths re-rooted (`/<root>/<sheet>` → `/<root>`); PCB untouched (it links by refdes
  — verified it contains no `(path)` bindings).
**Files touched:** `hardware/rtd-readout.kicad_sch` (rewritten), `hardware/unit_cell_ch1.kicad_sch`
+ `acquisition.kicad_sch` + `power_io.kicad_sch` (deleted), this log, `reports/review/` schematic
PDF regenerated. **Copper untouched.**
**Validation:**
- **Netlist oracle: node-for-node IDENTICAL** to pre-restructure (21 nets, same names, same
  (ref,pin) membership) — re-derived independently in the verification workflow.
- ERC **0 errors / 0 warnings**; DRC + schematic parity re-run (baseline 47 cosmetic items —
  no new categories).
- Visual audit of all 3 rendered pages + an adversarial spec-trace audit (workflow agents).
**Decisions:** blocks translated rather than redrawn (zero-risk to connectivity); cross-page
nets (CH2/CH3 taps + sense) stay as global labels — conventional and unavoidable; the
three-copies deviation note kept on page 1.
**Open issues / risks:** minor residual text overlaps inside J4 (pin names vs east labels) —
cosmetic; the sense-RC-filter decision (Session 006) still open before ordering.
**Next action:** Lucas audits page 1 against board_spec §Signal chain; then resolve the filter
decision and order.
**Commit:** on `schematic-readability`, merged to `main`.

---

## Session 006 — 2026-07-09 — rev-B: layout review + adversarial verify + real Digi-Key parts

**Tooling:** KiCad 10.0.3; Python 3.12.4; web research.
**Branch / commit at start:** `rev-b-parts` off `main` (rev-A).
**Objective:** Pre-order review — independently review the layout, adversarially verify it, put
real Digi-Key parts on the whole BOM, update schematic/BOM/fab, and package for Lucas's review.
**Actions:**
- **Layout review** (design + a background adversarial subagent told to refute): both converged.
  Verified against the copper: 4-layer split planes; GND split analog/digital with a genuine
  **single-point tie** (one 1.5 mm In1.Cu neck (80,50)→(83,50), the only bridge); no sensitive
  net crosses the split; +5V/VS power plane split; ADS beside R_ref; Kelvin intact; M3 corner
  holes DRC-clean. Verdict: **fabricable (yes-with-fixes).**
- **Parts:** researched real Digi-Key parts for every line. Two corrections: RTD conn
  **1729160 (6-pos) → 1729144 (4-pos)**; R_ref **Susumu 25 ppm → Vishay TNPU1206 ≤10 ppm**
  (board_spec binding). Updated MPN/Manufacturer per instance across all 5 sheets.
- Re-ran gates, re-exported BOM, regenerated fab, re-rendered 3D. Rewrote `reports/review/
  BOM_REVIEW.md` as the Digi-Key ordering list; updated `USER_MANUAL.md` (§8.4 review, §8.5
  open decision).
**Files touched:** `hardware/*.kicad_sch` (MPN fields only — nets/footprints/copper unchanged),
`reports/review/*`, `docs/USER_MANUAL.md`, this log.
**Validation:** ERC **0/0**; DRC **0 violations / 0 unconnected** (tag rev-B); BOM counts pass
(30 parts). SPICE unchanged. Parity still 47 (cosmetic; footprint MPN metadata not pushed).
**Open decision (Lucas):** **sense-line RC filter** (~1 kΩ+0.1 µF) is spec-required but absent
from schematic+board, and SPICE test5 models it — add (rev-C schematic+layout) or waive +
re-scope test5. Only item gating the order. Also: pick exact R_ref order code; confirm the
"◑ confirm at cart" Digi-Key P/Ns.
**Next action:** Lucas reviews `USER_MANUAL.md` §8.4/§8.5 + `BOM_REVIEW.md`; decide the filter;
then order from `fab/` (`fab-rev-B`).
**Commit:** rev-B parts + review; tags `rev-B`, `fab-rev-B`.

---

## Session 005 — 2026-06-25 — Track G: rev-A fab package + closeout

**Tooling:** KiCad 10.0.3; ngspice 44 (conda env `spice`); Python 3.12.4.
**Branch / commit at start:** `trackG` @ `c789a13` (off post-F integration; hardware frozen
at tag `rev-A` = `b630b5a`).
**State before:** A–F merged; ERC 0/0, DRC 0/0; no fab package; SPICE not yet re-pointed.
**Objective:** Generate the rev-A manufacturing package, final review artifacts, re-run SPICE
vs the real netlist, close out the design.
**Actions:**
- `scripts/run_gates --tag rev-A`, `scripts/fab_drop` (gerbers/drill/pos/STEP/BOM → `fab/`).
- Review artifacts → `reports/review/` (schematic PDF, 3D render, BOM_REVIEW, FAB_READINESS).
- Provisioned ngspice (conda) and re-ran `sim/scripts/run_all.py` vs `sim/netlists/rtd-readout.net`.
**Files touched:** `reports/{erc,drc,review}/**`, `docs/sessions/trackG.md`, this log; `fab/**`
(gitignored, captured by tag `fab-rev-A`). `hardware/**` untouched.
**Validation:**
- ERC 0/0; DRC 0 violations / 0 unconnected (rev-A).
- BOM vs board_spec: D=3, R=5 (3 R_ref + 2 pull-up), U=2, C=4, J=6, TP=10 — all pass; 30 parts.
- Stackup 4-layer / 1.6 mm; standard-fab DRC rules; Edge.Cuts present.
- SPICE: **all 7 tests PASS** vs the real netlist; reproduced Track B's `reports/sim/*.md`
  byte-identical (connectivity unchanged).
**Decisions:** fab cut from the rev-A-equivalent tree (cosmetic drawn-wire schematic only;
netlist identical); ngspice provisioned locally so the SPICE re-point ran here, not deferred.
**Open issues / risks:** 47 non-blocking parity items (mechanical/metadata); generic-passive
MPNs are placeholders; no panelization; **bench verification (TESTING_PLAN Part 2) needs the
physical board** — Lucas runs on assembly.
**Next action:** Lucas — order rev-A from `fab/` (`fab-rev-A`); run Part-2 bench on the
assembled board. **Design + fab package complete.**
**Commit:** trackG closeout; tag `fab-rev-A`. Integration merge of G is the final wave.

---

## Session 004 — 2026-06-25 — Integrate Track E wire-up + Track F (layout)

**Tooling:** KiCad 10.0.3 (`kicad-cli`).
**Branch / commit at start:** integration @ 8211249 (Tracks A–E merged; E at label-based version).
**State before:** Repo had been **moved** from `ivmux-python/excitation-current-source-v2` to
`Desktop/excitation-current-source-v2`, which broke all worktree git-links (stale gitdir
back-pointers). `trackE` was 2 commits ahead of integration (wire-up pass: drawn wires + power
symbols, `d19d202`); `trackF` (4-layer PCB, routed, `b630b5a`) was branched off integration but
unmerged. No `.kicad_pcb` in integration.

**Objective:** Merge the trackE wire-up pass, then merge trackF (layout), re-running ERC + DRC.

**Actions:**
1. `git worktree repair` on all six worktrees (rtd-integration, trackA–F) — fixed the stale
   gitdir links left by the repo move; all worktrees responsive again.
2. Verified ERC 0/0 on `trackE` tip before merging.
3. Merged `trackE` → integration (`--no-ff`, `e80ed2b`). Confirmed the netlist **connectivity
   is structurally identical** to pre-wire-up (net-name + node ref/pin extraction `diff` empty);
   the 62-line `.net` churn is export-date + regenerated tstamps/UUIDs + the deviation comment
   field only. So trackF's layout (built on the old netlist) is unaffected.
4. Merged `trackF` → integration (`--no-ff`, `2a5517b`). `.kicad_pro` merged with no conflict.

**Files touched:** merge commits only — `hardware/*.kicad_sch` (E), `hardware/rtd-readout.kicad_pcb`
(new, F), `hardware/rtd-readout.kicad_pro`, `sim/netlists/rtd-readout.net`, per-track logs;
this log entry.

**Validation:**
- ERC (merged): **0 errors / 0 warnings** (`kicad-cli sch erc --exit-code-violations`, exit 0).
- DRC (merged): **0 violations / 0 unconnected** (`kicad-cli pcb drc --schematic-parity`, exit 0).
- Schematic parity: **47 issues — pre-existing in trackF** (identical count + breakdown on the
  trackF tip before merge; the merge introduced none). Breakdown: 30 "missing MPN field in
  footprint" + 10 "Exclude-from-BOM differs" (footprint field/attribute metadata not
  back-synced from symbols — cosmetic), 4 extra + 3 duplicate footprints, **all with no
  reference designator** = mounting holes / fiducials placed without a schematic symbol
  (expected for mechanical footprints). None are net/connectivity errors.

**Decisions (rationale + spec ref):**
- trackE merged ahead of trackF — drawn-wire schematic is the canonical capture; netlist proven
  identical so it cannot disturb the existing layout.
- 47 parity issues accepted as non-blocking: DRC electrical is clean; issues are mechanical-
  footprint (no-symbol, expected) + un-synced metadata fields. — board_spec §Layout-critical.

**Open issues / risks:**
- Parity metadata (MPN field, BOM-exclude flags) is not synced PCB↔schematic. Harmless for
  routing/fab but should be tidied before a production BOM pull if MPNs are read off the board.
- trackF still owns the layout branch; integration now contains the board but `trackF` is not
  deleted. Track G (fab) runs off this post-F integration.

**Next action:** Track G — fab outputs (Gerbers/drill/BOM/pick-place) off this integration tip;
tag `rev-A` before any fab drop (per TRACK_F "Done when").
**Commit:** merges `e80ed2b` (E), `2a5517b` (F); this log entry committed as a follow-up.

---

## Session 003 — 2026-06-22 — Integrate Tracks A–E

**Tooling:** KiCad 10.0.3 (kicad-cli); ngspice/Python not on integrator PATH (Track B/C
re-run deferred to their owners' envs).
**Branch / commit at start:** integration @ a69b330 (Track A already merged).
**State before:** A merged. B (SPICE), C (host/bench), D (automation), E (schematic) complete
on their branches, reviewed, unmerged. Track sessions had landed review-feedback fixes (D:
`export_netlist --format spice`; E: recorded accepted 3-sheet deviation + cleaned loose
report artifacts).

**Objective:** Merge B→C→D→E into `integration` and re-gate the combined tree.

**Actions:**
- Merged in a dedicated `../rtd-integration` worktree, `--no-ff`, order B, C, D, E. **All four
  clean — zero conflicts** (paths disjoint; no track touched the global log).
- Re-ran gates on the merged tree via Track D's `scripts/run_gates --tag s003`.

**Merged (one summary per track):**
- **A** a69b330 — project-local symbol+footprint libs (10 parts); CRD polarity + ADS1115
  pinout verified vs datasheet.
- **B** 97f4f0c — SPICE harness (7 tests, models, accuracy/noise budget). Cross-cal
  cancellation + °C budget sound; test6/test7 claims to be softened (see open issues).
- **C** 1475f25 — `host/` acquisition lib + `test/` staged bench; ADS1115 register config and
  cross-cal math verified; 11/11 dry-run.
- **D** 35a3b05 — gate scripts, pre-commit hook, repo meta; kicad-cli flags valid for 10.0.3.
- **E** f2cc51b — hierarchical schematic (3 ch); ERC 0/0; netlist exported.

**Files touched:** merge of `sim/**`, `host/**`, `test/**`, `scripts/**`, `hardware/*.kicad_*`,
`docs/sessions/track{B..E}.md`, root `README.md`/`.gitignore`; `reports/erc/erc_s003.json`;
this log.

**Validation:**
- ERC: **0 errors / 0 warnings** on merged `hardware/rtd-readout.kicad_sch` (reports/erc/erc_s003.json);
  cross-checked with a direct `kicad-cli sch erc` run (exit 0).
- DRC: n/a — no PCB yet (run_gates SKIP, exit 0).
- SPICE / pytest: not re-run by integrator (toolchain not on PATH); accepted on track-owner
  evidence pending the test6/test7 wording fix.
- BOM cross-check (earlier): 3× CRD, 3× R_ref 910R, 2× ADS1115 (0x48/0x49), 2× 4.7k pull-ups,
  decoupling, 3 RTD + power + T7 connectors, 10 TPs — matches `board_spec.md` Resolved inputs.

**Decisions (rationale + spec ref):**
- **3 separate `unit_cell_chN` sheets** accepted (vs one reusable sheet ×3) for the frozen
  3-channel build — Lucas approved; recorded in `docs/sessions/trackE.md`. Trade-off: a future
  unit-cell edit must be applied 3×.

**Open issues / risks:**
- **Track B test6/test7 — RESOLVED in the merge** (trackB da2c103, verified in merged tree):
  test7 re-scoped to genuinely model the CMRR/shared-return path (not a metric artifact);
  test6 made conditional with the bench target back-solved — **max-allowable T7 noise =
  1.64 µV RMS** (at ADS 5 µV, BW 10 Hz). Track C Stage 5 must beat that on the real board.
  Residual caveat: test7 now rests on an *assumed* finite ADC CMRR — honestly stated, bench
  to confirm. No fab blocker remains from Track B.
- `lib.sh` severity-count display is cosmetic-buggy (`errors~00`); authoritative exit code is
  correct.
- `main` not advanced; `integration` holds A–E. Track branches/worktrees retained.

**Next action:** Start **Track F (layout)** off `integration` @ this commit — the serial spine.
Pt100 / 3-channel / star-ground + mixed-signal partition are the layout drivers
(`board_spec.md` §Layout-critical). Optionally fast-forward `main` to `integration` first.

**Commit:** 767a500 (Wave-0 closeout; this entry's hash backfilled by the immediate follow-up doc commit)

---

## Session 002 — 2026-06-22 — Resolve open inputs + stand up Wave-0 parallelism

**Branch / commit at start:** main @ 82efa90.
**State before:** Repo skeleton in place (Session 001). `board_spec.md` had 2 unresolved open
inputs gating Track E. No parallel branches yet.

**Objective:** Lock the two board decisions and set up the Wave-0 parallel mechanism so tracks
A–D can run.

**Actions:**
- Recorded Lucas's decisions in `docs/board_spec.md` (Open inputs → **Resolved inputs**).
- Created `integration` branch and Wave-0 worktrees `../rtd-trackA..D` per `PARALLEL_PLAN.md`.

**Files touched:** `docs/board_spec.md`, `docs/SESSION_LOG.md`.

**Validation:** ERC / DRC / SPICE — n/a (no design files yet).

**Decisions (rationale + spec ref):**
- **RTD type = Pt100** → T7 **±0.1 V** range — Lucas — `board_spec.md` §Resolved inputs #1.
- **3 RTD channels** → 3 CRD/R_ref unit cells, **2 ADS1115** (ADDR 0x48/0x49; 4 diff reads,
  1 spare), 3 RTD 4-wire connectors, 3 of 7 T7 Sense± pairs used — Lucas — §Resolved inputs #2.

**Open issues / risks:** none new. Pt100's small V_RTD (18–35 mV) makes T7 resolution-index
and mux settling the thing the bench plan must verify (Track C / Wave 3).

**Next action:** Hand each Wave-0 session its brief (`docs/tasks/TRACK_{A,B,C,D}_*.md`) in its
worktree; integrate **A first** (libraries gate the schematic), then B/C/D, then start **E**
off post-A `integration`.

**Commit:** cd7d0e7

---

## Session 001 — 2026-06-22 — Repo skeleton + doc relocation + reference vendoring

**Tooling:** KiCad <not yet pinned>, ngspice <not yet pinned> — to be recorded at first gate run.
**Branch / commit at start:** main @ 7c6b042 (Initial commit; only `.gitattributes` tracked, all docs loose in root).
**State before:** v2 doc set authored but sitting loose in the repo root. No directory structure.
Old (incomplete) REF200-based project dropped under `references/excitation-current-source/`
with its own nested git repo. New design abandons the **obsolete TI REF200**; current
excitation is now per-channel **CRD (1N5283/CDLL5283)** + R_ref, V_ref digitized by I²C
ADS1115s (see `docs/board_spec.md`).

**Objective:** Stand up the on-disk structure from `docs/DIRECTORY_MANAGEMENT.md` and relocate
the loose docs so `CLAUDE.md`'s `docs/...` paths resolve, making the repo ready for Wave-0
parallel sessions.

**Actions:**
- Created the directory tree per `DIRECTORY_MANAGEMENT.md`: `docs/{datasheets,sessions,tasks}`,
  `hardware/`, `libraries/{symbols,footprints,3dmodels}`, `sim/{models,netlists,scripts}`,
  `host/`, `test/{procedures,data}`, `scripts/`, `reports/{erc,drc,sim,test,bom}`. `.gitkeep`
  in each otherwise-empty dir. `fab/` left absent (generated + gitignored).
- Relocated the 7 process docs + `board_spec.md` from root → `docs/`.
- Relocated the 7 `TRACK_*.md` briefs from root → `docs/tasks/`.
- Authored `.gitignore` (adapted from the old project; base name `rtd-readout`).
- Vendored the old project as read-only reference: disabled its nested repo by renaming
  `.git` → `.git.disabled` (history preserved on disk, gitignored) so its files commit as
  plain reference and reach every worktree.

**Files touched:** `docs/**`, `docs/tasks/**`, directory skeleton, `.gitignore`,
`references/excitation-current-source/**` (vendored), `docs/SESSION_LOG.md`.

**Validation:** ERC / DRC / SPICE — n/a (no design files yet). Structure cross-checked
against `DIRECTORY_MANAGEMENT.md` layout.

**Decisions (rationale + spec ref):**
- **KiCad base name = `rtd-readout`** (not the old `ref200-rtd`) — matches the new track
  briefs (`hardware/rtd-readout.kicad_sch`, `sim/netlists/rtd-readout.net`) and
  `DIRECTORY_MANAGEMENT.md` §Naming. The old REF200 part is obsolete and out of the design.
- **lib-tables NOT pre-created** — `hardware/{sym,fp}-lib-table` are Track A's owned files;
  leaving them to A avoids a Wave-0 ownership collision (`PARALLEL_PLAN.md`).
- **Reference history preserved, not deleted** — `.git.disabled` keeps the old repo's history
  recoverable while avoiding an embedded-repo/submodule in this tree.

**Open issues / risks:**
- **Gates the schematic (Wave 1):** RTD type (Pt100 vs Pt1000 → T7 range) and how many of the
  7 channels are RTDs (→ CRD/R_ref/ADS1115 counts). `docs/board_spec.md` open inputs. Does
  NOT block Wave 0. Resolve with Lucas before Track E.
- `.git.disabled` is ignored, so the old git history lives only in this working tree — it will
  not propagate to other worktrees or a fresh clone (the reference *files* will).

**Next action:** Create the `integration` branch + Wave-0 worktrees (`rtd-trackA..D`) per
`PARALLEL_PLAN.md`; in parallel, Lucas resolves RTD type + channel count to unblock Wave 1 (E).

**Commit:** 01fd4e2 (bootstrap)

---

## Session 000 — (seed) — Project bootstrap

**Tooling:** KiCad <fill in>, ngspice <fill in>
**Branch / commit at start:** n/a

**State before:** Empty repository. Doc set in place; electrical design in
`docs/board_spec.md`. No KiCad project yet.

**Objective:** Stand up the repo skeleton and confirm the toolchain.

**Actions:**
- Create the directory structure per `docs/DIRECTORY_MANAGEMENT.md`.
- (To do) Initialize the KiCad project under `hardware/`.
- (To do) Stand up project-local libraries under `libraries/`.

**Files touched:** docs/, CLAUDE.md

**Validation:** ERC / DRC / SPICE — n/a (no design files yet).

**Decisions (rationale + spec ref):**
- **Architecture set:** per-channel CRD (1N5283/CDLL5283 ~220 µA) + stable R_ref; V_RTD on
  the T7's existing 7 differential pairs; V_ref digitized on-board by I²C ADS1115s (4 chips
  → 8 diff reads); **live ratiometric** with a per-channel cross-cal constant C, so source
  and R_ref values cancel — `board_spec.md` §"The measurement".
- **New accuracy term:** V_RTD and V_ref are on different ADCs → result carries G_T7/G_ADS;
  removed by one-time cross-cal, residual = R_ref tempco + relative ADC gain tempco. Keep
  both ADCs thermally stable, recal periodically — `board_spec.md` §"The measurement".

**Open issues / risks:**
- **Gates component values:** RTD type (Pt100 vs Pt1000 → T7 range) and how many of the 7
  channels are RTDs (→ CRD/R_ref/ADS1115 counts). See `board_spec.md` open inputs. Resolve
  with Lucas before capturing the repeated unit cell.
- CRD noise/dynamic-impedance and the relative-gain-tempco term are the two things the
  SPICE and bench plans must actually validate.

**Next action:** Confirm RTD type and channel count with Lucas; then initialize the KiCad
project and capture the single-channel unit cell (CRD + R_ref + RTD + ADS1115 V_ref tap)
per `board_spec.md`.

**Commit:** <fill in>
