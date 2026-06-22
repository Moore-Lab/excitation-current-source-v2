# Track B — SPICE Verification Harness — session log

Per-track log for Wave-0 Track B (see `docs/PARALLEL_PLAN.md`). Same schema as
`docs/SESSION_LOG.md`. Newest entry on top. The global log is updated only at integration.

---

## Session B-002 — 2026-06-22 — Adopt 200 µA (Mode A) as the design point

**Tooling:** ngspice 44, Python 3.12.4. **Branch / commit at start:** `trackB` @ b843cd1.

**State before:** Harness committed at the 100 µA design point (preset `pt100_100u`). Test 03
had shown the accuracy budget is ADC-offset-limited at 100 µA.

**Objective:** Re-run all decks at **200 µA** (Lucas) and, on the result, adopt 200 µA as the
SPICE design point.

**Actions:**
- Added preset `pt100_200u` to `config.py` — **Mode A** (both REF200 sources paralleled →
  1 channel/chip, 200 µA, output resistance halves to 25 MΩ), R_ref = 100 Ω, ±0.1 V range.
- Set `ACTIVE = pt100_200u` and re-ran `run_all.py`; all reports/params regenerated at 200 µA.

**Files touched:** `sim/scripts/config.py`, `sim/netlists/_generated_params.inc` (regen),
`reports/sim/*` (regen), `docs/sessions/trackB.md`.

**Validation:** `run_all.py` → exit 0. 200 µA vs 100 µA:
- 03 accuracy **raw single-read** 99.7%: **608 m°C** (was 1209) — offset-referred error
  **halved**, as predicted; max tolerable raw offset **1.3 µV** (was 0.7). Still > ±100 m°C,
  so 200 µA does **not** remove the need for offset nulling.
- 03 **nulled + 256× avg**: 59 m°C (was 61) — both currents land at the same ~20 m°C
  R_ref-limited floor; 200 µA's advantage there is marginal.
- 01/04 compliance 4.698 V (was 4.724) — negligibly less. 06 noise 216 nV (same chain, but
  2× signal → 2× SNR). 07 crosstalk 40 pV / 0.51 µ°C (4× coupling, still nil). 05 settling
  1.86 ms (was 1.72) — slightly worse step; per-channel-RC mitigation unchanged.

**Decisions (with rationale + spec ref):**
- **Adopt 200 µA / Mode A** (Lucas, 2026-06-22) — **reverses the Session-001 deviation** that
  chose 100 µA/Mode B. Buys 2× ADC-offset budget and 2× SNR (board_spec §3's original
  recommendation for Pt100), at the cost of **1 chip/channel** (3× REF200 for 3 ch, vs 2×
  in Mode B) and 4× self-heating (4 µW in R_ref — still negligible). Offset nulling is still
  required to meet ±0.1 °C.

**Cross-doc state — ALREADY RECONCILED upstream (verified at commit time):**
- The integrator had **already locked 200 µA / Mode A in `board_spec.md`** (commit `8c0f484`
  "spec: lock excitation at 200 uA / Mode A after T7 offset check", recorded in global
  `SESSION_LOG.md` Session 003) — acting on this track's test-03 ADC-offset finding — and
  added the Track E brief (200 µA / Mode A, `a063468`). board_spec §"Resolved configuration"
  now reads **200 µA, Mode A, 3× REF200, V_ref 20 mV**. So no Track-B reconciliation action
  remains; these 200 µA SPICE reports + config simply bring the harness into agreement with
  the already-updated spec.
- These two commits landed directly on `integration` (the shared working tree had been
  switched there by the integrator); since integration already carried the 200 µA spec lock
  and the merged Track-B harness, that is the consistent place for the regenerated reports.
- T7 measurement mode unchanged: full-differential, ±0.1 V range still fits (V_RTD max 31 mV).

**Next action:** None for Track B. Wave-3 re-point hook (modeled cell → KiCad netlist)
unchanged; Track E proceeds with Mode A.

**Commit:** c931609 (200 uA adoption on trackB)

---

## Session B-001 — 2026-06-19 — Build the full ngspice harness + accuracy/noise budget

**Tooling:** ngspice **44** (standalone CLI installed via `conda create -n ngspice -c
conda-forge ngspice` → `…/anaconda3/envs/ngspice/Library/bin/ngspice.exe`; KiCad's
`ngspice.dll` is not a CLI), Python 3.12.4 (numpy/scipy/matplotlib present), KiCad 10.0.3.
**Branch / commit at start:** `trackB` off `integration` @ db709f3.

**State before:** `sim/` was an empty skeleton (`models/`, `netlists/`, `scripts/` with
`.gitkeep`). `reports/sim/` empty. Resolved design point in `board_spec.md`: Pt100, 3 ch,
100 µA, Mode B, R_ref = 100 Ω, full-diff ±0.1 V AIN. Standalone ngspice was a known gap
(SESSION_LOG 001 risk).

**Objective:** Per `TRACK_B_spice.md` — build the headless ngspice harness and produce the
accuracy + noise budget against a modeled cell, parameterized by RTD type and R_ref, with
one report per test and a single `run_all` entry point.

**Actions:**
- Installed standalone ngspice (conda-forge env) — closes the Track B dependency risk.
- `sim/models/ref200.lib`: REF200 100 µA section = ideal DC source ∥ 50 MΩ (TI publishes
  **no** SPICE model — confirmed; documented in `models/README.md`). Noise handled per the
  README (Johnson natively in `.noise`; excitation current-noise added analytically).
- `sim/scripts/`: `rtd.py` (Callendar–Van Dusen Pt100/Pt1000 R↔T, validated vs IEC 60751
  reference points), `config.py` (one design point, presets + derived fields),
  `analysis.py` (parse/pass-fail/plots/Monte-Carlo→°C), `report.py` (TESTING_PLAN skeleton),
  `run_all.py` (single entry point; regenerates params, runs decks, writes reports).
- Seven decks in `sim/netlists/` (01 DC/compliance, 02 ratiometric, 03 accuracy-vs-R_ref,
  04 compliance corner, 05 sense settling, 06 `.noise`, 07 crosstalk). Sweeps via the
  behavioral-resistor + `.dc`-index trick; params shared via a generated `.param`/`.csparam`
  include.
- Harness hardening for this environment: ngspice is run in a **local temp copy** of the
  decks with **absolute `wrdata` paths** (rapid wrdata creation on the OneDrive-synced tree
  silently drops files; ngspice also doesn't resolve relative wrdata vs cwd reliably). Deck
  success judged from the log, not the spurious Windows exit code.

**Files touched:** `sim/models/{ref200.lib,README.md}`,
`sim/netlists/{01..07}*.cir`, `sim/netlists/_generated_params.inc`,
`sim/scripts/{rtd,config,analysis,report,run_all}.py`, `sim/scratch/.gitignore`,
`sim/README.md`, `reports/sim/{01..07}*.{md,png,log}`, `docs/sessions/trackB.md`.

**Validation:** `python sim/scripts/run_all.py` → exit 0. Per test (preset `pt100_100u`):
- 01 DC op / compliance: **PASS** — min source headroom 4.724 V (≫ 2.5 V).
- 02 ratiometric: **PASS** — max |R_calc−R_RTD| = 6.0e-10 ppm (exact; independent of I and
  R_out, the architectural guarantee).
- 03 accuracy → °C: **CONDITIONAL** — R_ref-limited floor **20 m°C** (confirms the spec
  sanity check). Full budget is **ADC-offset-dominated at 100 µA** (10 mV signals): raw
  single-read 99.7% = **1209 m°C (FAILS)**; with per-channel offset nulling + 256× averaging
  = **61 m°C (meets ±100 m°C)**. Ratiometric cancels gain and source current but NOT ADC
  offset.
- 04 compliance corner: **PASS** — worst-corner headroom 4.724 V.
- 05 sense settling: **CONDITIONAL** — a shared 0.1 µF needs ~1.72 ms to settle vs the 1 ms
  dwell; mitigated by **per-channel RC before the mux** (caps never re-settle) or smaller C.
- 06 noise: **PASS** — 216 nV RMS chain (Johnson 203 nV + excitation) ≪ 1.4 µV ADC floor.
- 07 crosstalk: **PASS** — 10 pV (0.26 µ°C) at R_star 0.05 Ω; coupling = R_star·R_RTD/R_out.

**Decisions (with rationale + spec ref):**
- **Model REF200 as ideal source ∥ 50 MΩ** — no TI model exists; matches TESTING_PLAN model
  strategy (datasheet R_out 20–100 MΩ).
- **Accuracy MC + °C mapping in Python, not ngspice** — the ratiometric relation is exact in
  SPICE (deck 02), so the budget is a closed-form/MC propagation of R_ref tol+tempco and ADC
  offset/gain/noise; ngspice ideal sources can't carry the statistical/offset terms. Honest
  and more defensible than a fragile ngspice MC.
- **Surface the ADC-offset finding as the headline** — board_spec's 100 µA deviation note
  anticipated reduced SNR; this quantifies that the limiter is ADC **offset** (averaging does
  not remove offset), requiring per-channel offset nulling. `t7_offset` (8 µV) is a flagged
  assumption to verify against the T7 datasheet.
- **Run ngspice in a local temp dir with absolute wrdata paths** — robust workaround for the
  OneDrive-synced tree dropping rapidly-created files.

**Open issues / risks:**
- **T7 ADC offset spec unverified** — `t7_offset` and `t7_noise_rms` in `config.py` are
  assumptions (datasheets not yet in repo — Track A). The accuracy verdict hinges on these;
  confirm against the LabJack T7-Pro ±0.1 V range spec.
- **Two CONDITIONALs feed downstream:** (a) bench plan must add per-channel ADC offset
  nulling + averaging (Stage 2/3); (b) Track F layout must place the sense RC **per channel,
  before the T7 mux**. If offset can't be nulled below ~0.7 µV, reconsider 200 µA (Mode A).
- ngspice not on PATH and returns spurious non-zero exit codes on Windows — handled in
  `run_all.py` (auto-discovery + log-based success), but note for any new tooling.

**Next action:** At **Wave 3**, re-point the decks from the modeled cell to the KiCad-exported
netlist `sim/netlists/ref200-rtd.net` (procedure in `sim/README.md` "Wave-3 hook"); re-run
`run_all.py` and confirm the numbers hold against the as-designed circuit.

**Commit:** 91dcbb9 (harness + reports on `trackB`; this hash line in the follow-up commit).
Note: this work was first committed while the shared working tree had been switched to
`trackD` by a parallel session, so the originals (e287e72/e101a0f) landed on `trackD`. They
were cherry-picked onto `trackB` here and removed from `trackD` to restore clean per-track
separation.
