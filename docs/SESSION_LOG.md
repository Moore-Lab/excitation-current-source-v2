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
