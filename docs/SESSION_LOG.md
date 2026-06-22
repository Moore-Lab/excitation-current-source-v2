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
