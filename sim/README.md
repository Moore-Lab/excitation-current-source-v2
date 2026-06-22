# sim/ — SPICE verification harness (Track B)

Headless ngspice proof that the RTD-readout circuit is correct and a quantified
accuracy/noise budget, built on a **modeled** circuit before the board exists.
Implements TESTING_PLAN Part 1. Pt100, 3 channels (`docs/board_spec.md`).

## Layout

```
sim/
├── models/        shared, reused by every deck
│   ├── params.inc   design nominals (CRD, R_ref, gains, Pt100 sweep window)
│   ├── crd.inc      current-regulator diode: I_src || finite Z_dyn, scalable
│   ├── meas.inc     the two ADCs as ideal differential gain blocks (T7, ADS1115)
│   ├── knobs.inc    sweep/perturbation variables carried as node voltages
│   └── channel.inc  one unit cell (CRD + R_ref + RTD + both ADC reads)
├── netlists/      one deck per TESTING_PLAN Part-1 test (test1..test7)
└── scripts/
    ├── spice_io.py  ngspice locator, wrdata loader, report writer, constants
    └── run_all.py   single entry: run decks -> analyse -> plots + reports
```

## Run it

```bash
# from the repo root
python sim/scripts/run_all.py            # run all decks, analyse, write reports
python sim/scripts/run_all.py --no-run   # re-analyse existing data only
```

Outputs (committed): one report per test in `reports/sim/*.md` and plots in
`reports/sim/plots/`. Intermediate `reports/sim/{data,logs}/` are regenerable and
gitignored. Exit code is non-zero if any test FAILs.

## ngspice

Needs the **console/batch** build (`ngspice_con` / `ngspice -b`). The harness
auto-detects it via, in order: `$NGSPICE_BIN`, a conda env named `spice`, then
`PATH`. Provision once with conda-forge (portable, no system install):

```bash
conda create -y -n spice -c conda-forge ngspice      # ships ngspice_con.exe
```

Pinned/validated: **ngspice-41**. KiCad bundles only `ngspice.dll` (no CLI), so a
standalone batch binary is required.

## What each test proves (all PASS on the modeled circuit)

| Deck | Proves | Headline result |
|------|--------|-----------------|
| test1 | CRD stays in compliance over the Pt100 sweep at the low rail | min V_CRD 4.26 V ≫ V_L 1.05 V |
| test2 | cross-cal recovers R; invariant to ±10 % CRD / R_ref | error ~7e-9 (numerical floor) |
| test3 | MC accuracy → °C, dominated by R_ref + relative gain tempco | σ ≈ 0.038 °C @ 10 ppm/°C, ΔT 10 °C |
| test4 | worst-case V_ref under ADS1115 range | 221 mV = 86 % FS, 14.8 bits |
| test5 | sense RC settles < ½ LSB within mux dwell | 1.0 ms < 5 ms |
| test6 | ratio noise below target; CRD-noise risk bounded | 13 m°C; CRD bound 2.9 nA/√Hz worst case |
| test7 | shared-ground crosstalk below floor | ~0 at 0.1 Ω star-ground |

Bench-measurable assumptions (T7/ADS noise, mux dwell, targets) are named
constants at the top of `run_all.py`; drop in real datasheet/bench numbers there.

## Architecture notes worth knowing

- **Knobs as node voltages.** `dt, tcref, tcgr, off, kc, kref, rrtd` are 0-impedance
  voltage sources; behavioral models read them as `v(knob)`. This lets every deck
  sweep/perturb headlessly with `alter` (no re-parse) and is why the RTD is swept
  with a plain `.dc Vrrtd ...`.
- **Two ADCs.** `G_T7` and `G_ADS` are independent; the entire *relative* gain
  tempco lives on the T7 path (only the ratio matters). This is the new accuracy
  term vs the old series-chain design.
- **CRD noise cancels** in the ratio under simultaneous sampling (same current in
  V_ref and V_RTD). test6 bounds the i_n that would matter if sampling were *not*
  simultaneous — the one architectural risk to watch on the bench (Stage 8).

## Wave-3 hook — re-point at the exported KiCad netlist

Today the topology is modeled in `models/channel.inc`. When Track E's schematic
exists, Wave 3 exports `sim/netlists/rtd-readout.net` and the decks can read the
**real** netlist instead of the model. The analysis layer (`run_all.py`) is
topology-agnostic — it only depends on this **node/knob contract**, so keep these
names in the export (or add a thin alias `.include`):

- nodes: `rail`, `top` (R_ref top / V_ref+), `mid` (R_ref bottom = V_ref− = RTD top),
  measurement outputs `nref` (ADS read) and `nrtd` (T7 read);
- knob sources from `knobs.inc` still present (`dt, tcref, tcgr, off, kc, kref, rrtd`);
- the CRD modeled by `crd.inc` and the ADC reads by `meas.inc` (the real board
  digitizes off-deck, so these gain blocks stay as the measurement model).

Concretely: replace the `.include sim/models/channel.inc` line in each deck with
`.include sim/netlists/rtd-readout.net` once it presents the same nodes, re-run
`run_all.py`, and the same pass/fail criteria apply unchanged.