# Track C — session log

Per-track development record (parallel mode). **Newest entry on top.** Same schema as
`docs/SESSION_LOG.md`. Track C owns `host/**` and `test/**`; reports go to `reports/test/`.

---

## Track C / Session 001 — 2026-06-22 — Acquisition library (`host/`) + staged bench procedures (`test/`)

**Review follow-up (post-commit):** Track C passed review (ADS1115 register config, cross-cal +
ratiometric math, time-alignment, 0x48/0x49 addressing all verified; 11/11 dry-run). Applied the
three minor robustness items: (1) `ads1115._read_once` now raises `IOError` on conversion
timeout instead of reading stale data after the OS-poll falls through; (2) `stage8_crd_noise`
guards each V_ref read so an unresponsive ADS fails its gate rather than crashing the stage;
(3) `None`-defaulted `n_avg`/`ads_navg` retyped `Optional[int]` in `ads1115`/`acquire`. Added
`test_ads_conversion_timeout_raises`; dry-run self-test now **12/12** (pytest 12 passed),
pyflakes/flake8 still clean.


**Tooling:** Python 3.12.4 (anaconda3), numpy 1.26.4, pyflakes 3.2.0, flake8 7.0.0, pytest 7.4.4.
KiCad/ngspice — n/a for this track.
**Branch / commit at start:** `trackC` @ d54eb69 (clean, off `integration`/`main`).
**State before:** `host/` and `test/` were empty skeletons (`.gitkeep` only). The vendored old
project (`references/excitation-current-source/`) held a complete *single-ADC, REF200,
series-chain* bench harness — reused as a structural template, not copied.

**Objective:** Write the reusable acquisition library (`host/`) and the staged bench
procedures (`test/`) for the **dual-ADC** design so that the moment the board exists Lucas
runs the tests with no glue work. No hardware needed; dry-run against a mock.

**Brief-name discrepancy (surfaced for Lucas):** the kickoff handed this session
`docs/tasks/TRACK_C_libraries.md`, which does not exist. Track C is unambiguously
**Acquisition + Bench** (`TRACK_C_bench.md`, `PARALLEL_PLAN.md`, the ownership matrix all
agree); "libraries" is **Track A**. Treated `_libraries` as a typo and proceeded as Track C.
No action needed unless the dispatcher meant to launch Track A here.

**Actions (ordered):**
1. Kickoff: read brief, `SESSION_KICKOFF`, `board_spec` (§measurement/components/interfaces),
   `TESTING_PLAN` Part 2, `DIRECTORY_MANAGEMENT` (host/ vs test/); verified env + worktree.
2. Studied the vendored old harness end-to-end for patterns (backend abstraction, CVD math,
   datalog schema, gate/report scaffolding, the position-independence statistic).
3. Built `host/` (acquisition library):
   - `config.py` — `BoardConfig` + the two converter maps (T7 diff pairs for V_RTD; ADS1115
     chip/address/MUX for V_ref), parameterized for Pt100/Pt1000 and 1–7 channels
     (`ceil(n/2)` ADS1115 at 0x48–0x4B). Defaults = resolved design point.
   - `transport.py` — one device, two surfaces: `Transport` (analog + I²C), real `LJMTransport`
     (T7 over LJM; I²C via the LJM I2C register block on the same handle), and a **mock that
     models the ADS1115 at the I²C-register level** so the real driver's register pack/unpack
     is exercised in dry runs. Scenario builders (nominal + series-chain).
   - `t7_rtd.py` — T7 V_RTD driver (range/resolution/settling/neg-channel; software averaging).
   - `ads1115.py` — ADS1115 V_ref driver: config/conversion register protocol, single-shot +
     OS-bit poll, PGA/MUX/DR encode, differential read with N-conversion averaging, bus scan.
   - `acquire.py` — `BoardSession`: the time-aligned per-channel dual read → `{V_RTD, V_ref}`.
   - `measurement.py` — cross-cal math: `R = C·V_RTD/V_ref`, `C = R_known·V_ref/V_RTD`.
   - `calibration.py` — persist/load per-channel C (`cross_cal.json`, schema `rtd-crosscal/1`).
   - `rtd.py`, `paths.py` — CVD R<->T (reused) and repo-relative locations.
4. Built `test/` (bench harness + procedures):
   - `bench/` — `datalog.py` (CSV+meta, schema `rtd-bench/1`), `stats.py` (noise / position
     independence / baseline compare), `report.py` (TESTING_PLAN skeleton), `baseline_gen.py`
     (synthetic series-chain placeholder), `common.py` (CLI, gates, board build, prompts,
     in-situ cross-cal bootstrap for standalone dry runs).
   - `procedures/` — Stage 0–8 to the **new** TESTING_PLAN numbering + `run_all.py`.
   - `tests/test_dryrun.py` — hardware-free self-test (host math + every stage).
   - `requirements.txt`, `README.md`, `data/README.md`, committed baseline placeholder.
5. Ran gates; fixed: unused imports; Windows console UTF-8 (`±/Ω/I²C` crashed cp1252 →
   stdout reconfigure); `baseline_gen` import bootstrap; Stage 6 averaging; Stage 5 sample
   count for the 7-ch position-independence estimator.

**Files touched:** `host/{__init__,config,transport,t7_rtd,ads1115,acquire,measurement,calibration,rtd,paths}.py`;
`test/bench/{__init__,datalog,stats,report,baseline_gen,common}.py`;
`test/procedures/{__init__,stage0_poweroff_checks,stage1_power_i2c,stage2_cross_cal,stage3_ratiometric,stage4_real_rtd,stage5_noise_position,stage6_crosstalk,stage7_thermal_soak,stage8_crd_noise,run_all}.py`;
`test/tests/{__init__,test_dryrun}.py`; `test/{requirements.txt,README.md,data/README.md}`;
`test/data/baselines/example_series_chain.{csv,meta.json}`; `docs/sessions/trackC.md`.
Removed redundant `host/.gitkeep`, `test/procedures/.gitkeep`, `test/data/.gitkeep`.

**Validation (numbers):**
- ERC / DRC / SPICE — n/a (Track C touches no KiCad/sim files).
- Lint: `pyflakes host test` clean; `flake8 --select=F,E9 host test` clean; `compileall` clean.
- Dry-run self-test: `python tests/test_dryrun.py` → **11/11 passed**; `pytest -q` → **11 passed**.
  Covers: CVD round-trip; I²C scan returns expected chips (3ch→0x48/0x49, 7ch→0x48–0x4B);
  cross-cal recovers a known R to <0.2 %; **CRD current value cancels in the ratio** (±30 %
  current → recovered R unchanged); position-independence detector flags series-chain growth;
  full Stage 0–8 sequence passes for **Pt100 (3ch)**, **Pt1000 (3ch)**, **Pt100 (7ch)**;
  Stage 5 **FAILs** a synthetic series-chain board; Stage 8 **FAILs** a noisy CRD (3000 ppm).
- Spot numbers (mock): cross-cal C ≈ 909.9 Ω (≈ R_ref 910, gains ideal); R-recovery worst
  ~0.007 %; per-channel temp noise ~15–40 mK (< 50 mK floor).

**Decisions (rationale + spec ref):**
- **Two driver layers over one transport** — on the bench a single T7 reads V_RTD (analog) and
  drives the ADS1115 I²C bus (digital). Modeled as one `Transport` with both surfaces, so the
  mock and the real device share a call surface — `board_spec.md` §"Board as the hub".
- **Mock simulates I²C at the register level** (not a V_ref shortcut) so `ads1115.py`'s real
  protocol code runs in dry runs — higher fidelity, catches encode/decode bugs pre-hardware.
- **C is mandatory for recovery** — without cross-cal a cross-ADC ratio is not a resistance;
  `compute_channel` requires C. Downstream stages bootstrap an in-situ C in mock so each stage
  is runnable standalone; Stage 2 writes the authoritative file on the bench —
  `board_spec.md` §"The measurement".
- **New TESTING_PLAN stage numbering** adopted (Stage 5 = noise/position headline, Stage 7 =
  C-drift soak, Stage 8 = CRD noise) — differs from the old vendored harness; matches
  `TESTING_PLAN.md` Part 2 and the brief.
- **R_ref default 910 Ω, ADS PGA ±0.256 V** — V_ref ≈ 0.78·FS at nominal current with CRD
  +10 % headroom — `board_spec.md` §"Reference resistor".
- **Stage 6 averages 32 reads / Stage 5 needs a long record** — crosstalk is a quasi-DC shift
  (average below budget); the position-independence std-of-std estimator spreads at low n with
  many channels (finite-sample artifact, not real position dependence) — bench uses long runs.

**Open issues / risks:**
- `LJMTransport` is **untested against silicon** (no LJM here). The I²C register sequence
  (SLAVE_ADDRESS / NUM_BYTES_TX-RX / DATA_TX / GO / ACKS / DATA_RX) and the ADS1115 OS-poll
  are written from the datasheet/LJM docs; the bench operator validates in Stage 1. SDA/SCL
  DIO line numbers in `config` (default FIO0/1) must match the actual T7 wiring.
- Mock noise figures (T7 ~3 µV, ADS ~2 LSB, CRD 30 ppm) are order-of-magnitude placeholders;
  reconcile gates against Track B's SPICE budget at integration (Wave 3).
- Synthetic `example_series_chain.csv` is a placeholder — replace with Lucas's real old-board
  log and point Stage 5 at it via `--baseline`.

**Next action:** Hold for integration (libraries/Track A merge first per `PARALLEL_PLAN`).
At Wave 3, run `host/` + `test/` against the real T7 (validate `LJMTransport` in Stage 1),
swap in the real series-chain baseline, and reconcile gate thresholds with Track B's budget.

**Commit:** HEAD of branch `trackC` (this entry's commit; not merged — integration pulls
Track A first per `PARALLEL_PLAN.md`).
