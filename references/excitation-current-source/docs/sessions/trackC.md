# Track C — session log (bench procedures & T7 control)

Per-track log for parallel Wave-0 work (see `docs/PARALLEL_PLAN.md`). Newest entry
on top. Same schema as `docs/SESSION_LOG.md`. Merged into the global log at
integration.

---

## Track C — 2026-06-19 — Bench bring-up suite + T7 control (hardware-free)

**Tooling:** Python 3.12.4, numpy 1.26.4. KiCad/ngspice not used (Track C touches no
KiCad/SPICE files). `labjack-ljm` + LJM runtime NOT installed here (real-T7 path is
bench-only; mock path needs neither).
**Branch / commit at start:** `trackC` @ db709f3 (branched off `integration`).

**State before:** `test/` held only `.gitkeep` placeholders. No bench procedures or
T7 control code existed.

**Objective:** Deliver the full staged bring-up (Stage 0→8) and the LabJack T7 Pro
control/data-logging code so Lucas can run the bench tests with no glue work the
moment the board exists — written, import/lint-clean, and dry-run-verified against a
mock with no hardware. Parameterized for Pt100 and Pt1000.

**Actions:**
- **Config layer** (`test/config/board_config.py`): single source of truth, derives
  spec defaults per RTD type; generates the T7 AIN map per measurement mode
  (full-diff 4 AIN/ch max 3; SE-subtract 3 AIN/ch max 4; calibrated-current 2 AIN/ch
  max 7 — board_spec §5). Default = resolved config (Pt100/3ch/100 µA/100 Ω/full-diff/±0.1 V).
- **T7 control** (`test/t7/`): abstract `T7Backend` + factory; `ljm_backend.py` (real
  T7 over LJM, lazy import); `mock_backend.py` (hardware-free board physics sim with
  configurable per-channel noise — nominal *position-independent* and synthetic
  *series-chain* scenarios); `board.py` (`BoardSession`: configures range/resolution/
  settling/negative-ch, collapses all 3 modes to `{V_ref, V_RTD}`).
- **Support lib** (`test/lib/`): `rtd.py` (Callendar–Van Dusen R↔T, both RTD types,
  Newton for T<0); `measurement.py` (ratiometric + calibrated-current recovery);
  `calibration.py` (per-channel current constants JSON); `datalog.py` (CSV + meta-JSON,
  one stable schema); `stats.py` (noise, **position-independence verdict**, baseline
  compare); `report.py` (TESTING_PLAN report skeleton → `reports/test/`); `baseline_gen.py`
  (synthetic old-board placeholder); `paths.py`.
- **Procedures** (`test/procedures/`): runnable script per stage 0–8 + `common.py`
  (shared CLI/gates/operator prompts) + `run_all.py` (sequence driver). Stage 2 writes
  `calibration.json`; Stage 3 does ratiometric substitution accuracy; Stage 6 is the
  headline noise + position-independence test with direct old-vs-new comparison.
- **Tests/docs**: `test/tests/test_dryrun.py` (7 checks), `test/README.md`,
  `test/requirements.txt`, `test/data/README.md`, committed labeled synthetic baseline.
- Compile-linted all modules; ran the self-test and full sequence in both Pt100 and
  Pt1000.

**Files touched:** `test/README.md`, `test/requirements.txt`, `test/config/**`,
`test/t7/**`, `test/lib/**`, `test/procedures/**`, `test/tests/**`, `test/data/README.md`,
`test/data/baselines/example_series_chain.{csv,meta.json}`, `docs/sessions/trackC.md`.

**Validation:**
- ERC: n/a (Track C touches no schematic). DRC: n/a (no PCB). SPICE: n/a.
- Lint: `python -m py_compile` clean across config/lib/t7/procedures/tests.
- Dry-run self-test: **7/7 passed** (`test/tests/test_dryrun.py`). Includes RTD
  round-trip (<1e-3 °C), ratiometric recovery (<0.2 %), and the negative test —
  Stage 6 correctly **FAILS** on a series-chain (position-dependent) board.
- Full Stage 0→8 sequence: **PASS** for Pt100/3ch and Pt1000/3ch; **PASS** for
  Pt1000/7ch calibrated-current. Mock Stage-3 accuracy worst-case ≈0.017 %; mock
  Stage-6 per-channel noise ≈33–41 mK, spread ≤1.24× (position-independent).

**Decisions (with rationale + spec ref):**
- **Hardware-free, mock-backed architecture** (`T7Backend` abstraction) — so the whole
  suite lints and dry-runs with no LJM/board, per the brief's "Done when".
- **Fully parameterized for Pt100/Pt1000 + 3 modes** via `make_config`/presets — the
  RTD-type decision can't force a rewrite (brief; board_spec §3/§5).
- **One stable CSV schema + JSON meta sidecar; reports via shared skeleton** — so old
  runs and the old series-chain baseline always load and bench/SPICE reports compare
  (TESTING_PLAN report format; DIRECTORY_MANAGEMENT — `test/data` committed).
- **Synthetic series-chain baseline committed as a labeled placeholder** — exercises
  the Stage-6 comparison tooling now; to be replaced by Lucas's real old-board log.
- **Stage gate thresholds are starting values** (Stage 6 floor 100 mK / spread 1.5×;
  Stage 3 0.2 %; Stage 2 ±1 %; compliance ≥2.5 V) — all CLI-overridable.

**Open issues / risks:**
- `labjack-ljm` + LJM runtime absent here → `ljm_backend.py` is untested against
  silicon; the operator validates it in Stage 1. The mock path is fully exercised.
- Gate thresholds are placeholders — **reconcile with Track B's SPICE noise/accuracy
  budget at integration** so the bench gates match the predicted floor.
- Shared working tree contains other tracks' untracked files (libraries/, sim/,
  hardware/lib-tables). Track C committed **only** `test/**` + this log (ownership
  respected). Base `integration` has no `.gitignore` (Track D); used local
  `.git/info/exclude` for `__pycache__` so artifacts aren't staged.
- **Branch-collision incident (resolved):** the Wave-0 sessions are sharing ONE
  working tree (not the per-session worktrees `PARALLEL_PLAN.md` recommends). A
  concurrent Track D session switched HEAD to `trackD` mid-session, so Track C's
  two commits first landed on `trackD`. Corrected by cherry-picking them onto a
  clean `trackC` (from db709f3, in an isolated worktree) and resetting `trackD`
  back to its tip (3636e96). Future Wave-0 sessions should use separate worktrees.

**Next action:** At integration, set the Stage-6/Stage-3 gates from Track B's SPICE
numbers; when the board exists, run `python procedures/run_all.py --real`, and point
Stage 6 at the real old series-chain dataset via `--baseline`.

**Commit:** 44bcc5d (Track C suite on `trackC`; this hash line in the follow-up commit)
