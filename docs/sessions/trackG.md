# Track G — Fab Outputs & Closeout (session log)

Per-track log, newest entry on top. Schema mirrors `docs/SESSION_LOG.md`.

---

## Track G — 2026-06-25 — rev-A fab package + closeout

**Tooling:** KiCad 10.0.3 (`kicad-cli`); ngspice 44 via conda env `spice`
(`conda create -n spice -c conda-forge ngspice`); Python 3.12.4.
**Branch / commit at start:** `trackG` @ `c789a13`, branched off post-F `integration`
(Tracks A–F merged; hardware frozen at tag `rev-A` = `b630b5a`).
**State before:** integration carried the drawn schematic (E) + 4-layer routed board (F),
ERC 0/0, DRC 0/0. No fab package generated; SPICE not yet re-run against the real netlist.

**Objective:** Produce the manufacturing package from the tagged `rev-A` board, generate
final review artifacts, re-run the SPICE harness against the real netlist, and close out.

**Actions:**
1. Re-ran gates via `scripts/run_gates --tag rev-A` → `reports/{erc,drc}/*_rev-A.json`.
2. Cut the fab drop via `scripts/fab_drop` → `fab/` (gitignored): gerbers (4-layer),
   drill, position CSV, STEP, fab BOM.
3. Final review artifacts → `reports/review/`: schematic PDF, top 3D render (PNG),
   `BOM_REVIEW.md` (count cross-check vs board_spec), `FAB_READINESS.md` (stackup/rules).
4. Stood up ngspice in a conda `spice` env and re-ran `sim/scripts/run_all.py` against the
   real exported netlist (`sim/netlists/rtd-readout.net`).

**Files touched (owned deliverables):** `reports/erc/erc_rev-A.json`,
`reports/drc/drc_rev-A.json`, `reports/review/**`, `fab/**` (gitignored, captured by tag),
this log + `docs/SESSION_LOG.md`. `hardware/**` untouched (frozen at rev-A).

**Validation (with numbers):**
- ERC **0 errors / 0 warnings**; DRC **0 violations / 0 unconnected** (at rev-A).
- BOM cross-check vs board_spec (3-channel): D=3 (CRD=channels), R=5 (3 R_ref + 2 pull-ups),
  U=2 (ADS1115=ceil(3/2)), C=4 (2 decap + 2 bulk), J=6, TP=10 — **all rules pass**; 30 parts.
- Stackup: **4 copper layers** (F/In1/In2/B.Cu), 1.6 mm, Edge.Cuts outline present.
  Rules: 0.25/0.5 mm tracks, 0.6–0.8 mm vias, 0.2 mm min hole, 0.13 mm clearance —
  standard-fab manufacturable.
- **SPICE: all 7 tests PASS** against the real netlist (T1 DC compliance margin 3.21 V;
  T2 ratio/xcal err ~7e-9 « 1e-6 tol; T3 MC sigma 0.038 °C; T4 V_ref 86% FS / 14.8 bit;
  T5 settle 1.02 ms < 5 ms dwell; T6 noise 13.2 m/20 mC; T7 crosstalk 1.6e-5 °C/Ω). The
  re-run reproduced Track B's committed `reports/sim/*.md` **byte-identical** (connectivity
  unchanged since B's run).

**Decisions (rationale + spec ref):**
- Fab generated from the current trackG tree (hardware identical to tag `rev-A` =
  `b630b5a`; the only intervening change was the cosmetic drawn-wire schematic, netlist
  proven identical). Captured with tag `fab-rev-A`.
- ngspice provisioned locally (conda) so the closeout SPICE re-point actually ran here,
  rather than deferring to the Track B env. `spice` env documented above for reproducibility.

**Open issues / risks:**
- 47 schematic-parity items persist (mechanical footprints w/o symbols + un-synced footprint
  metadata) — non-blocking, documented in SESSION_LOG Session 004.
- Generic-passive MPNs are placeholders; assign at order time (see `BOM_REVIEW.md`).
- **Panelization** not done (single-board outline) — add at the fab portal if required.
- **Bench verification** (TESTING_PLAN Part 2: cross-cal / noise / thermal drift / CRD-noise)
  needs the physical board — Lucas runs on the assembled unit. Procedures are ready (Track C).

**Next action:** Lucas — (1) order rev-A from `fab/` (tag `fab-rev-A`); (2) on the assembled
board, run TESTING_PLAN Part 2. Design/fab side is complete.
**Commit:** this entry committed with the rev-A reports; tag `fab-rev-A` on the closeout.
