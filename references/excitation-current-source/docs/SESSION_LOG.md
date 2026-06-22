# SESSION_LOG.md

Running development record for the REF200 RTD board. **Newest entry on top.** The session
kickoff reads the top entry to recover state. Every session must end by appending a new
entry here (see the schema) and committing.

## Entry schema (copy this block for each new session)

```
## Session NNN — YYYY-MM-DD — <short objective>

**Tooling:** KiCad <x.y.z>, ngspice <x.y>, <other>
**Branch / commit at start:** <branch> @ <hash>

**State before:** <one or two sentences: what existed and what passed>

**Objective:** <what this session set out to do>

**Actions:**
- <ordered list of what was actually done>

**Files touched:** <paths>

**Validation:**
- ERC: <N errors / M warnings> (report: reports/erc/...)
- DRC: <N violations> (report: reports/drc/...)
- SPICE: <which tests ran, pass/fail vs acceptance criteria> (reports: reports/sim/...)

**Decisions (with rationale + spec ref):**
- <decision> — <why> — <board_spec.md section / datasheet ref>

**Open issues / risks:**
- <anything unresolved, fragile, or needing Lucas input>

**Next action:** <the single exact next step the next session should take>

**Commit:** <hash that captures this end state>
```

---

## Session 003 — 2026-06-22 — Verify T7 offset spec; lock excitation at 200 µA / Mode A

**Tooling:** WebFetch (LabJack T-Series datasheet). No build tools used.
**Branch / commit at start:** integration @ 8fd4e59.

**State before:** Integration (Session 002) flagged the headline risk — at 100 µA the accuracy
budget is **ADC-offset-limited** and hinged on an *assumed* `t7_offset = 8 µV`. Decision on
100 µA vs 200 µA deferred pending the real T7 spec.

**Objective:** Verify the LabJack T7-Pro ±0.1 V offset spec and resolve the excitation current
before Track E captures the schematic.

**Actions:**
- Fetched the T7 AIN general specs (LabJack datasheet A-3-2-1). **±0.1 V range (Gain=100):**
  absolute accuracy **±20 µV** (offset+gain+linearity; offset *not* broken out separately),
  noise **<1 µV p-p / 22-bit eff.**, tempco **15 ppm/°C** (all ranges), input bias **20 nA**,
  max source impedance **1 kΩ**.
- Worked the budget: offset-referred error = R_ref·δ/V_ref → **~26 m°C per µV at 100 µA**,
  **~13 m°C per µV at 200 µA**. Unnulled ~20 µV offset = ~520 m°C (100 µA) — fails ±100 m°C.
  **Per-channel offset nulling is mandatory at either current**; the differentiator is margin.
- **Lucas's decision: 200 µA / Mode A** — doubles V_ref/V_RTD (20 mV / 16–31 mV), halves the
  offset-referred error (comfortable ~30 m°C after nulling), robust against the unspecified
  offset drift, for one extra REF200 per channel (3 chips, no spare). Self-heating still 4 µW.
- Updated `board_spec.md`: "Resolved configuration" → 200 µA / **Mode A** / 3× REF200 /
  V_ref 20 mV / V_RTD 16–31 mV (R_ref 100 Ω unchanged); replaced the Session-001 100 µA
  deviation note with the offset-driven 200 µA rationale + the mandatory-nulling requirement +
  the verified T7 numbers. Corrected §6: **T7 bias = 20 nA, not pA** → the planned 1 kΩ sense
  series-R drops 20 µV/line (common-mode only if matched; prefer 100–200 Ω matched); and the
  **sense RC must be per-channel before the mux** (Track B deck 05).

**Files touched:** `docs/board_spec.md`, `docs/SESSION_LOG.md`.

**Validation:** N/A (spec/research + doc updates). T7 numbers sourced from LabJack datasheet
A-3-2-1.

**Decisions (with rationale + spec ref):**
- **200 µA / Mode A** — `board_spec.md` Resolved configuration; supersedes the Session-001
  100 µA choice. Driven by the offset-limited budget (Track B deck 03) + the ±20 µV T7 abs
  accuracy. Now *aligned* with §3's "Pt100 → 200 µA" rule of thumb.
- **Per-channel offset nulling + averaging is a firm requirement** (not optional) — neither
  current meets ±100 m°C unnulled.

**Open issues / risks:**
- **Track B's committed accuracy reports are at 100 µA** — they remain valid analysis but no
  longer match the locked design. **Re-run the SPICE budget at 200 µA** (update
  `sim/scripts/config.py` current + set `t7_offset` from the ±20 µV abs-accuracy bound) to
  confirm the ~30 m°C margin against the as-decided point. Tracked, not blocking Track E.
- **Track C bench Stage-2/3 must implement per-channel offset nulling**; reconcile gate
  thresholds with the (re-run) 200 µA budget.
- **Track F layout:** per-channel sense RC *before* the mux; sense series-R 100–200 Ω matched
  (not 1 kΩ) given 20 nA bias.

**Next action:** Start **Wave 1 — Track E (schematic)** in its own session off `integration`,
using Track A's libs (`ref200-rtd` nickname), REF200 in **Mode A** (pins 8+7→+5 V, pins 1+2→
R_ref→RTD per chip, pin 6→GND, pins 3/4/5 NC), one REF200 per channel (3 total), R_Precision
for R_ref, LP2985-5.0 power, screw terminals. Bake in per-channel sense RC + offset-null
provision.

**Commit:** 8c0f484 (board_spec 200 µA/Mode A + T7 findings; this hash line in follow-up)

---

## Session 002 — 2026-06-19 — Integrate Wave-0 Tracks A–D

**Tooling:** KiCad 10.0.3 (off PATH), ngspice 44 (standalone, installed by Track B via
conda-forge; not on PATH), Python 3.12.4 + numpy 1.26.4.
**Branch / commit at start:** integration @ db709f3; four track branches (`trackA`–`trackD`)
each branched from db709f3 with work + log-hash commits.

**State before:** Wave-0 ran as **four separate interactive sessions** (the background-subagent
route was abandoned — background jobs have no human to approve permission prompts, so every
mutating tool was auto-denied; see the `.claude/settings.json` allowlist commit db709f3 that
did not reach the sandboxed background workers). All four tracks completed and committed to
their branches. The OneDrive working tree also held **stale untracked duplicate copies** of
Track A/C files (verified older than the committed branches — e.g. `trackC.md` working copy
lacked the branch-collision note and referenced a superseded hash).

**Objective:** Integrate the four disjoint tracks into `integration` in dependency order,
verify the result, and record the cross-track findings.

**Actions:**
- Confirmed the four tracks are **path-disjoint** (A=`libraries/`+lib-tables+`docs/datasheets/`,
  B=`sim/`+`reports/sim/`, C=`test/`, D=`.gitignore`+`README.md`+`scripts/`; each only its own
  `docs/sessions/trackX.md`).
- Stashed the stale OneDrive duplicates (`stash@{0}`, verified-older dupes; OneDrive locks left
  empty dirs but git tree was clean) and merged **A → B → C → D** with `--no-ff`. **Zero
  conflicts.** Integration HEAD = 674611f.
- Verified the integrated tree (not trusted): `scripts/run_gates` → ERC/DRC **SKIP, exit 0**
  (graceful, no schematic/PCB yet); Track C `test/tests/test_dryrun.py` → **7/7 pass**.

**Files touched:** four `--no-ff` merge commits (190368f A, d8711b0 B, 65a8c3e C, 674611f D);
`docs/SESSION_LOG.md` (this entry). No source files hand-edited at integration.

**Validation:**
- ERC/DRC: n/a (no schematic/PCB) — `run_gates` SKIP/SKIP exit 0 (verified this session).
- Track A: `kicad-cli sym/fp upgrade` exit 0; 9/9 symbols + 9/9 footprints render; **REF200AU
  pin map 8/8 = `board_spec.md` §2**.
- Track B (`run_all.py` exit 0, reports committed): 01 DC/compliance PASS (4.724 V headroom),
  02 ratiometric PASS (exact, 6e-10 ppm), 03 accuracy **CONDITIONAL**, 04 PASS, 05 settling
  **CONDITIONAL**, 06 noise PASS (216 nV ≪ 1.4 µV floor), 07 crosstalk PASS (10 pV).
- Track C: dry-run **7/7** (verified this session); full Stage 0–8 PASS for Pt100/3ch and
  Pt1000 (mock); Stage 6 correctly FAILS a synthetic series-chain (negative test works).
- Track D: `run_gates` acceptance cases all pass (SKIP→0, clean→0, violations→1, malformed→1).

**Decisions (with rationale + spec ref):**
- **Merge per-branch from the authoritative commits; discard the stale OneDrive working-tree
  dupes** — verify-don't-trust caught `trackC.md` working copy as older than committed. Stash
  kept as a reversible safety net.
- **R_ref part = Vishay VSMP1206 `Y1625100R000Q9R` (0.02 %, 0.2 ppm/°C Z-foil)** — Track A.
  Deviation from the 0.01 % *tolerance* target, but the firm spec is ≤10 ppm/°C tempco (this is
  ratiometric → tempco dominates), which 0.2 ppm/°C beats ~50×. 0.01 % grade is a drop-in.

**Open issues / risks (cross-track — feed Wave 1+):**
- **HEADLINE — accuracy at 100 µA is ADC-offset-limited, not R_ref-limited (Track B deck 03).**
  R_ref floor is 20 m°C, but a raw single read is **1209 m°C (FAILS ±100 m°C)**; with
  **per-channel ADC offset nulling + 256× averaging → 61 m°C (PASS)**. Ratiometric cancels gain
  and source current but **not** ADC offset. ⇒ (a) bench Stage 2/3 must add offset nulling +
  averaging; (b) the `t7_offset`=8 µV assumption in `sim/scripts/config.py` **must be verified**
  against the LabJack T7-Pro ±0.1 V spec; (c) if offset can't get below ~0.7 µV, reconsider
  **200 µA / Mode A** (revisits the Session-001 100 µA deviation).
- **Sense RC must be per-channel, before the T7 mux (Track B deck 05).** A shared 0.1 µF needs
  ~1.72 ms vs the 1 ms dwell → layout constraint for Track F; bench scan rate ties in.
- **Bench gate thresholds are placeholders (Track C)** — reconcile with Track B's budget
  (Stage-6 floor, Stage-3 accuracy) so bench gates match the predicted floor.
- **T7 ADC offset/noise specs not yet in repo** — datasheet needed (the accuracy verdict hinges
  on it). Track A could not auto-download TI/Vishay/LabJack PDFs (anti-bot); URL-referenced.
- **Parallel execution used a shared working tree, not per-track worktrees** → a branch-collision
  incident (Track B/C commits briefly landed on `trackD`, cherry-picked back; resolved). Future
  Wave-0-style parallel work must use real `git worktree` per track.
- **Root `.gitattributes` is `* text=auto`** → LF→CRLF on Windows checkout (the persistent git
  warnings). Track D scoped `*.sh eol=lf` locally; consider hoisting `eol=lf` for `*.sh`,
  `*.cir`, `*.kicad_*` to the root file.
- ngspice 44 lives in a conda env (not on PATH); `run_all.py` auto-discovers it. Document the
  env or add to PATH for reproducibility.

**Next action:** Start **Wave 1 — Track E (schematic)** off `integration`, using Track A's libs
(nickname `ref200-rtd`), REF200 in **Mode B** (pin 8/7→+5 V, 1/2→R_ref→RTD, 6→GND, 3/4/5 NC),
R_Precision for R_ref, LP2985-5.0 power, screw terminals per the BOM in `trackA.md`. Bake in the
two CONDITIONAL findings: **per-channel sense RC before the mux** and a plan for **per-channel
ADC offset nulling**. Verify the T7 offset spec early — it gates the 100 µA decision.

**Commit:** 7fa92e2 (integration = A+B+C+D merged @ 674611f + this entry; hash line in follow-up)

---

## Session 001 — 2026-06-19 — Resolve design inputs, fix doc misprints, stand up skeleton

**Tooling:** KiCad **10.0.3** (`C:\Program Files\KiCad\10.0\bin\kicad-cli.exe` — **not on PATH**),
ngspice: **no standalone CLI** (only `ngspice.dll` bundled in KiCad), Python 3.12.4.
**Branch / commit at start:** main @ a0774a3 (only `.gitattributes` committed; `docs/` was untracked)

**State before:** Process/doc framework authored but uncommitted; no repo skeleton; the two
gating design inputs (RTD type, channel count) open; filename references in the docs did not
match the actual files; a `docs/parallel sessions/` parallel-work plan present.

**Objective:** Resolve the RTD-type/channel-count blocker, fix doc misprints, create the
directory structure per `DIRECTORY_MANAGEMENT.md`, and commit an `integration` base for
Wave-0 parallel work.

**Actions:**
- Recorded resolved inputs in `board_spec.md` (Pt100, 3 channels → 100 µA, Mode B, 2× REF200,
  R_ref = 100 Ω, full-differential 4-wire, ±0.1 V AIN).
- Fixed filename misprints by renaming files to the canonical names the docs already reference:
  `SESSION_KICKOFF_1.md`→`SESSION_KICKOFF.md`, `REF200_RTD_board_spec.md`→`board_spec.md`;
  moved `docs/CLAUDE.md`→`/CLAUDE.md` (root, so Claude Code auto-reads it). Zero reference edits
  needed (all references already used the canonical names).
- Fixed BOM-export path typo in `BOARD_DEV_CHECKLIST.md` (`reports/sim/../bom/`→`reports/bom/`).
- Moved the parallel-work plan to the canonical paths its own text references
  (`docs/PARALLEL_PLAN.md`, `docs/tasks/TRACK_*.md`); removed the `docs/parallel sessions/`
  space-in-path folder; created `docs/sessions/` for per-track logs.
- Created the directory skeleton (`hardware/`, `libraries/{symbols,footprints,3dmodels}`,
  `sim/{models,netlists,scripts}`, `scripts/`, `test/{procedures,data}`,
  `reports/{erc,drc,sim,test,bom}`, `docs/datasheets/`) with `.gitkeep` placeholders.
- Verified toolchain (see Tooling) — surfaced two install gaps as risks below.
- Committed the result on a new `integration` branch as the Wave-0 base (`main` left at a0774a3).

**Files touched:** `CLAUDE.md` (moved), `docs/SESSION_KICKOFF.md` (renamed),
`docs/board_spec.md` (renamed + resolved-config section), `docs/BOARD_DEV_CHECKLIST.md`,
`docs/SESSION_LOG.md`, `docs/PARALLEL_PLAN.md` + `docs/tasks/TRACK_*.md` (moved),
`docs/sessions/.gitkeep`, new skeleton dirs + `.gitkeep`s.

**Validation:**
- ERC: n/a (no schematic yet)
- DRC: n/a (no PCB yet)
- SPICE: n/a (no decks yet; standalone ngspice not installed — see risks)

**Decisions (with rationale + spec ref):**
- **Pt100, 3 channels** — Lucas, 2026-06-19 — closes `board_spec.md` open inputs.
- **100 µA / Mode B / 2 REF200 / R_ref 100 Ω / full-diff 4-wire** — `board_spec.md`
  "Resolved configuration". **Deviation from §3** (which recommends 200 µA for Pt100): chosen
  for 2 ch/chip density (2 chips for 3 ch + spare), lower self-heating, and ~10 mV signal still
  ≫ T7 noise floor at a cost of ≈1 bit SNR. Revisit if Stage-6 noise is excitation-limited.
- **Rename-not-edit** to fix filename misprints — fewer touch points, preserves the docs'
  intended canonical names.
- **Will run Wave-0 parallel sessions (Tracks A–D)** — Lucas — so `README.md`/`.gitignore`/
  `scripts/**` are reserved for Track D and intentionally absent from the base commit.
- **Parallel docs moved to match references** (not references edited) — removes the
  space-in-path that would break the worktree/CLI flow.

**Open issues / risks:**
- **Standalone ngspice missing.** Track B's `ngspice -b deck.cir` flow has no binary
  (only KiCad's `ngspice.dll`). Install standalone ngspice before Track B runs.
- **kicad-cli not on PATH.** Track D's gate scripts must use the full path
  (`C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`) or amend PATH; pin KiCad **10.0.3**.
- **Base `integration` has no `.gitignore`** (reserved for Track D). Until Track D merges it,
  Wave-0 worktrees should avoid committing ignorable artifacts (KiCad backups/`.kicad_prl`,
  `sim/scratch/`, `libraries/_verify/`, `__pycache__/`).

**Next action:** Spin up Wave-0 sessions A–D from worktrees off `integration`
(`git worktree add ../ref200-trackX -b trackX integration`), handing each its brief in
`docs/tasks/`. In parallel, install a standalone ngspice (Track B dependency). Wave 1
(schematic, Track E) waits on Track A + the resolved design decision.

**Commit:** f3869b7 (skeleton + resolved docs on `integration`; this log-hash line in the
immediate follow-up commit)

---

## Session 000 — (seed) — Project bootstrap

**Tooling:** KiCad <fill in>, ngspice <fill in>
**Branch / commit at start:** n/a

**State before:** Empty repository. Doc set in place (`CLAUDE.md`, `docs/`). Electrical
design captured in `docs/board_spec.md`. No KiCad project files yet.

**Objective:** Stand up the repository skeleton and confirm the toolchain.

**Actions:**
- Created directory structure per `docs/DIRECTORY_MANAGEMENT.md`.
- (To do) Initialize KiCad project under `hardware/`.
- (To do) Set up project-local symbol/footprint libraries under `libraries/`.

**Files touched:** docs/, CLAUDE.md

**Validation:**
- ERC: n/a (no schematic yet)
- DRC: n/a (no PCB yet)
- SPICE: n/a

**Decisions (with rationale + spec ref):**
- Ratiometric topology with per-channel reference resistor adopted as the design baseline
  — removes REF200 absolute-accuracy and drift from the result — `board_spec.md` §"Measurement equation".

**Open issues / risks:**
- **BLOCKER for component values:** RTD type (Pt100 vs Pt1000) and total channel count are
  unresolved — see the two open inputs at the bottom of `board_spec.md`. These set current
  (200 vs 100 µA), R_ref (100 Ω vs 1 kΩ), chips-per-channel, and the AIN measurement mode.
  Resolve with Lucas before schematic capture of the repeated unit cell.

**Next action:** Confirm RTD type and channel count with Lucas, then initialize the KiCad
project and create the single-channel unit-cell schematic per `board_spec.md` §1–§2.

**Commit:** <fill in>
