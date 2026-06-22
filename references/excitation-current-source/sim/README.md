# sim/ — SPICE verification harness (Track B)

ngspice test harness + accuracy/noise budget for the REF200 RTD board, built **before**
the board exists against a modeled unit cell. Proves the circuit is correct and quantifies
the accuracy/noise budget per `docs/TESTING_PLAN.md` Part 1.

## Run it

```bash
python sim/scripts/run_all.py                 # active preset (Pt100, 100 µA, R_ref 100 Ω)
python sim/scripts/run_all.py --preset pt1000_100u
python sim/scripts/run_all.py --ngspice /path/to/ngspice
```

`run_all.py` is the single entry point. It (1) regenerates `netlists/_generated_params.inc`
from `scripts/config.py`, (2) runs all seven decks headless, (3) parses each, decides
pass/fail, plots, and writes `reports/sim/<test>.md` + `.png`, (4) prints a summary and
exits non-zero on any hard FAIL (CONDITIONAL does not fail). Re-running fully regenerates
`reports/sim/` — never hand-edit those.

### ngspice

Needs a **standalone ngspice CLI** (`ngspice -b`). KiCad ships only `ngspice.dll`, which is
not a CLI. Install one and the runner auto-discovers it (`$NGSPICE`, PATH, then a conda
`ngspice` env):

```bash
conda create -n ngspice -c conda-forge ngspice
```

Python deps: numpy, scipy, matplotlib (already present in the project env).

## Layout

```
sim/
├── models/
│   ├── ref200.lib      # REF200 100 µA section: ideal source ∥ 50 MΩ (no TI model exists)
│   └── README.md       # model strategy, noise handling, where to drop a TI model
├── netlists/
│   ├── _generated_params.inc   # GENERATED from config.py (committed copy = active preset)
│   ├── 01_dc_op.cir            # DC operating point & compliance margin
│   ├── 02_ratiometric.cir      # ratiometric correctness (R_calc = R_ref·V_RTD/V_ref)
│   ├── 03_accuracy_rref.cir    # SPICE sensitivity of recovered R to R_ref deviation
│   ├── 04_compliance_corner.cir# worst-case compliance corner
│   ├── 05_transient_settling.cir# sense RC settling vs mux dwell
│   ├── 06_noise.cir            # .noise of passive/Johnson chain through the filter
│   └── 07_crosstalk.cir        # shared star-ground crosstalk
├── scripts/
│   ├── config.py       # ONE design point (presets + derived); edit here to re-target
│   ├── rtd.py          # Callendar–Van Dusen Pt100/Pt1000 R<->T (maps ΔR -> ΔT in °C)
│   ├── analysis.py     # parse, pass/fail, plots, Monte-Carlo accuracy -> °C
│   ├── report.py       # render a result into the TESTING_PLAN markdown skeleton
│   └── run_all.py      # single headless entry point
└── scratch/            # raw ngspice wrdata (gitignored; runner actually uses a temp dir)
```

The deck/output paths are decoupled from the source tree: the runner stages a **local
temp copy** of the decks/models and runs ngspice there, because rapid `wrdata` file
creation in this OneDrive-synced tree silently drops files. `sim/scratch/` stays empty in
normal operation; the committed `_generated_params.inc` keeps the decks runnable by hand.

## Re-targeting (Pt100 ↔ Pt1000, R_ref, etc.)

Everything keys off `scripts/config.py`. Change `ACTIVE`, or a preset's `r_ref` / `i_exc`
/ `t7_*`, and re-run — decks, params, and reports all follow.

## Wave-3 hook — swap the modeled cell for the real netlist

These decks model the unit cell directly. At fabrication (Track G), KiCad exports the real
netlist to `sim/netlists/ref200-rtd.net`. To re-validate against the as-designed circuit:

1. Export from KiCad: `kicad-cli sch export netlist --format spice -o sim/netlists/ref200-rtd.net hardware/ref200-rtd.kicad_sch`.
2. In each deck, replace the inline unit-cell elements (the `Vrail`/`Xsrc`/`Rref`/`Rrtd`
   block) with `.include netlists/ref200-rtd.net` and an `X` call to the exported subckt,
   keeping the same node names for the sense/ref taps so the `.control` math is unchanged.
3. Re-run `run_all.py`; the pass/fail criteria and reports are identical, now against the
   real netlist. Confirm the numbers still hold (especially compliance and noise).

## Current results (preset `pt100_100u`)

| Test | Verdict | Headline |
|------|---------|----------|
| 01 DC op / compliance | PASS | min source headroom 4.72 V (≫ 2.5 V) |
| 02 ratiometric | PASS | R_calc error < 1e-9 ppm (exact, I/R_out-independent) |
| 03 accuracy → °C | **CONDITIONAL** | R_ref floor 20 m°C; meets ±0.1 °C only with per-channel offset null + averaging (offset, not R_ref, dominates at 100 µA) |
| 04 compliance corner | PASS | worst-corner headroom 4.72 V |
| 05 sense settling | **CONDITIONAL** | needs per-channel RC (before mux) or smaller C; a shared 0.1 µF needs ~1.7 ms > 1 ms dwell |
| 06 noise | PASS | 216 nV RMS chain ≪ 1.4 µV ADC floor |
| 07 crosstalk | PASS | 10 pV (0.26 µ°C) at R_star 0.05 Ω |

The two CONDITIONALs are design/measurement requirements for downstream tracks, not circuit
failures — see the respective reports for the exact actions (offset nulling + averaging;
per-channel sense RC placement).
