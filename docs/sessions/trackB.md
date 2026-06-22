# Track B — SPICE verification harness — session log

Newest entry on top. Schema per `docs/SESSION_LOG.md`. This is Track B's effective
kickoff/closeout record; the global `SESSION_LOG.md` is touched only at integration.

---

## TrackB-002 — 2026-06-22 — Integration-review fixes (test7 re-scope, test6 conditional)

**Branch / commit at start:** trackB @ bed8256.

**State before:** TrackB-001 harness, all 7 PASS. Integration review accepted the
harness, test2 (cancellation) and test3 (°C budget), but flagged 2 MAJOR + 2 nit items.

**Objective:** Resolve the review without overclaiming; stay in `sim/**`, `reports/sim/**`.

**Actions (by review item):**
1. **[MAJOR] test7 measured nothing.** The victim metric `v(nrtdB)/v(nrefB)` cancels
   the channel current algebraically, so every `test7_rg_*.dat` was bit-identical — the
   "zero" was cancellation by construction, not a numerical floor. Re-scoped (reviewer's
   option a): added a **finite-CMRR** term to `meas.inc` (`cmrr` subckt param, default
   1e12 = effectively infinite, so tests 1–6 are untouched). test7 now sets ADC CMRR
   (T7 90 dB, ADS 105 dB) and sweeps the **aggressor current** over its ±10 % CRD spread
   (the quantity that actually moves the shared-return common mode `v(sg)=(I_A+I_B)·RG`);
   the victim couples only through finite CMRR. Files now differ monotonically with RG.
2. **[MAJOR] test6 PASS rode on assumed T7 noise.** Restated as a **conditional** PASS
   and back-solved the **max-allowable T7 noise** the bench must beat:
   **T7 ≤ 1.64 µV RMS** (at ADS 5 µV, BW 10 Hz, 20 m°C target). Report + README updated;
   the only physically-derived (Johnson) terms are ~0.05 m°C, stated plainly.
3. **[NIT] encoding.** `spice_io.write_report` now writes `encoding="utf-8"` (the em-dash
   was emitting cp1252 0x97). Verified no lone 0x97 byte remains.
4. **[NIT] STAR_GND no-op.** With real coupling, `t7` now fits coupling = k·RG, reports
   coupling at the 0.1 Ω budget and the max RG meeting target — the budget constant is used.

**Files touched:** `sim/models/meas.inc`, `sim/netlists/test7_crosstalk.cir`,
`sim/scripts/{run_all,spice_io}.py`, `reports/sim/{test6_noise,test7_crosstalk}.md`,
`reports/sim/plots/{test6_noise,test7_crosstalk}.png`, `sim/README.md`, this log.

**Validation (re-ran full harness; all 7 still PASS):**
- tests 1–5 **numerically unchanged** (e.g. test2 err 7.5e-9 / 6.6e-9, test3 σ 0.0376 °C) —
  confirms the CMRR=1e12 default does not perturb the accepted results.
- test6: **conditional PASS** — 13.2 m°C at assumed T7 1 µV / ADS 5 µV (1.5× margin);
  **max-allowable T7 = 1.64 µV RMS** surfaced for the bench; CRD bound 2.9 nA/√Hz worst case.
- test7: **PASS, now non-zero** — coupling 1.6 µ°C at 0.1 Ω, linear at 1.6e-5 °C/Ω,
  max R_gnd ≈ 1.3 kΩ for the 20 m°C target (so crosstalk is not the binding constraint,
  but it is measured, not zero).

**Decisions (rationale + spec ref):**
- **CMRR as the crosstalk path** — with a ratiometric differential metric, shared-return
  coupling can *only* enter via finite common-mode rejection; modeling CMRR is the honest
  mechanism. `board_spec.md` §Layout-critical (star ground = shared-return crosstalk path).
- **test6 stays conditional, not "PASS"** — the physically-derived noise is negligible, so
  the result is only as good as the ADC-noise assumptions; the back-solved T7 limit is the
  actionable deliverable for Track C.

**Open issues / risks (carried + new):**
- T7/ADS noise, BW, mux dwell, settle target remain **assumptions** (named in `run_all.py`).
  test6's headline is explicitly gated on them; bench must confirm **T7 ≤ 1.64 µV**.
- **Track D coordination:** the Wave-3 re-point needs a **SPICE** netlist; D's
  `export_netlist` currently emits KiCad s-expr. Integration must run
  `kicad-cli sch export netlist --format spice`. Flagged in `sim/README.md` (Wave-3 hook);
  not Track B's owned step.

**Next action:** Hand back for integration. At Wave 3, produce the SPICE-format
`sim/netlists/rtd-readout.net` and re-point per `sim/README.md`.

**Commit:** da2c103 (review fixes + this entry); hash recorded in the follow-up.

---

## TrackB-001 — 2026-06-22 — Build the full ngspice harness + accuracy/noise budget

**Tooling:** ngspice-41 (conda-forge `ngspice_con.exe`, env `spice`); Python 3.12.4
(Anaconda) with numpy 1.26 / matplotlib 3.8 / scipy 1.13. KiCad 10.0 present but
ships only `ngspice.dll` (no batch CLI) — hence the standalone ngspice.

**Branch / commit at start:** trackB @ d54eb69 (worktree `../rtd-trackB`).

**State before:** Wave-0 start. `sim/{models,netlists,scripts}` and `reports/sim/`
empty except `.gitkeep`. No SPICE work yet. board_spec resolved: Pt100, 3 channels.

**Objective:** Stand up the headless ngspice harness for all 7 TESTING_PLAN Part-1
tests on a *modeled* circuit, parameterized by RTD type and R_ref, and produce a
concrete accuracy (°C) + noise budget before the board exists.

**Actions:**
1. Resolved a brief mismatch first: my hand-off named `TRACK_B_libraries.md` (does
   not exist). Confirmed with Lucas — this is **Track B = SPICE** (the `B` label),
   not Track A (libraries). Proceeded on `sim/**`, `reports/sim/**`.
2. Provisioned ngspice: SourceForge scripted downloads were anti-bot-blocked, so
   installed conda-forge `ngspice` into env `spice` (Lucas chose "portable, non-repo").
   Verified headless batch (`ngspice_con -b`) on a smoke deck.
3. Authored shared models: `params.inc`, `crd.inc` (I_src ‖ finite Z_dyn, scalable),
   `meas.inc` (T7 & ADS1115 as ideal diff gain blocks with tempco/offset), `knobs.inc`
   (sweep vars as node voltages), `channel.inc` (one unit cell).
4. Wrote 7 decks (`test1..test7`); validated each headless. De-risked three ngspice
   idioms by probe: `.dc` sweep of a behavioral RTD resistor; in-`.control` Monte-Carlo
   with `sgauss(0)` + `set rndseed` (reproducible) accumulated via `set appendwrite`
   (vectors don't survive per-`op` plot switches); `.noise` needs an `AC` input and the
   spectral plot is reached with `setplot previous`.
5. Wrote `sim/scripts/spice_io.py` (ngspice locator, wrdata loader, report writer) and
   `run_all.py` (single entry: run → analyse → plots + reports + pass/fail summary).
6. Ran the whole harness; all 7 PASS. Wrote one report per test + plots; added local
   `.gitignore`s and `sim/README.md` with the Wave-3 re-point hook.

**Files touched:** `sim/models/{params,crd,meas,knobs,channel}.inc`,
`sim/netlists/test{1..7}_*.cir`, `sim/scripts/{spice_io,run_all}.py`, `sim/README.md`,
`sim/.gitignore`, `reports/sim/test{1..7}_*.md`, `reports/sim/plots/*.png`,
`reports/sim/.gitignore`, `docs/sessions/trackB.md`. (Removed obsolete `.gitkeep`s in
the now-populated `sim/` subdirs.)

**Validation (SPICE — all vs TESTING_PLAN Part-1 criteria; reports/sim/*.md):**
- test1 DC/compliance: **PASS** — min V_CRD 4.26 V at 4.5 V rail ≫ V_L 1.05 V (margin 3.21 V); V_RTD 17.7–34.9 mV (matches spec 18–35 mV).
- test2 ratio+cross-cal: **PASS** — R_calc error 7e-9 (CRD ±10 %, nominal C) / 7e-9 (R_ref ±10 %, own recal) — invariance at the numerical floor.
- test3 Monte-Carlo accuracy: **PASS** — σ = 0.0376 °C (analytic RSS 0.0380 °C) at 10 ppm/°C R_ref + 10 ppm/°C relative gain over ΔT 10 °C; tempco terms (0.0256 °C each) dominate offset (0.0116 °C). Reproducible across reruns (`rndseed`).
- test4 R_ref sizing: **PASS** — V_ref 221 mV at +10 % CRD = 86 % of ADS ±0.256 V FS, 14.8 effective bits (< 90 % FS).
- test5 sense RC settling: **PASS** — settles to ½-LSB (1 µV) in 1.02 ms < assumed 5 ms mux dwell (τ ≈ 100 µs).
- test6 ratio noise: **PASS** — 13 m°C (Johnson + assumed T7/ADS noise) < 20 m°C target; CRD current-noise bound 2.9 nA/√Hz worst case (non-simultaneous), ~0 if sampled simultaneously.
- test7 crosstalk: **PASS** — victim coupling ~0 (numerical floor) at 0.1 Ω star-ground; Kelvin + current-source isolation makes it negligible for realistic ground R.

**Decisions (rationale + spec ref):**
- **ngspice via conda-forge env `spice`, not vendored into the repo** — keeps binaries
  out of git; `run_all.py` auto-detects (NGSPICE_BIN → conda → PATH). board_spec/PLAN
  imply a batch ngspice; KiCad ships none.
- **Knobs encoded as node voltages** (`dt,tcref,tcgr,off,kc,kref,rrtd`) — lets every
  deck sweep/perturb headlessly with `alter`; RTD swept via `.dc Vrrtd`. Enables the
  in-deck Monte-Carlo. (Engineering choice; no spec conflict.)
- **Relative gain tempco carried entirely on the T7 path** — only the ratio matters;
  `board_spec.md` §"The measurement" (limiter = R_ref tempco + relative ADC gain tempco).
- **Noise budget is analytic on top of ngspice Johnson PSD** — ngspice `.noise` gives
  source-impedance-correct Johnson; custom CRD current-noise PSDs aren't natural in
  `.noise`, and the CRD term is best framed as a *bound* (TESTING_PLAN #6). Documented.

**Open issues / risks:**
- T7 / ADS1115 input noise (1 µV / 5 µV RMS), effective measurement BW (10 Hz), mux
  dwell (5 ms), and the ½-LSB settle target (1 µV) are **assumptions**, named at the top
  of `run_all.py`. Replace with datasheet/bench numbers (Track C / Wave 3) — they move
  test5/test6 margins but not the architecture conclusion.
- **The offset term scales as 1/V_RTD** (~22 mV for Pt100): if T7/ADS offset drift is
  worse than ~1 µV it can rival the tempco terms in test3. Worth watching on the bench.
- test2/test7 "pass at numerical floor" — correct physically (cancellation/Kelvin), but
  the residuals are at solver tolerance, not a measured small number. Stated in-report.

**Next action:** Commit on `trackB` (do not merge). At Wave 3, export the KiCad netlist
to `sim/netlists/rtd-readout.net` and re-point the decks per the node/knob contract in
`sim/README.md` (replace the `.include channel.inc` line), then re-run `run_all.py`.

**Commit:** 0617208 (harness + reports + this log); hash recorded in the follow-up.
