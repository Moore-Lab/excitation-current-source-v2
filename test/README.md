# Bench bring-up & acquisition (Track C)

Staged bring-up procedures (`test/`) driving the reusable acquisition library
(`host/`) for the **dual-ADC** RTD readout board. The moment the physical board
exists, Lucas runs the staged tests with no glue work left. Everything runs
**with no hardware** against a mock transport, so the procedures are written,
linted, and dry-run-verified ahead of fab.

Maps to `docs/TESTING_PLAN.md` Part 2 (Stages 0–8) and uses the shared report
skeleton. Parameterized for **Pt100 and Pt1000** and **up to 7 channels** so the
RTD-type / channel-count decisions never require a rewrite. Default config = the
resolved design point (Pt100, 3 ch, ~240 µA, R_ref ≈ 820 Ω, T7 ±0.1 V, ADS1115
±0.256 V, 2 chips at 0x48/0x49).

## The measurement (board_spec.md "The measurement")

Two ADCs, one ratiometric result with a per-channel cross-cal constant **C**:

```
R_RTD = C · (V_RTD / V_ref)            V_RTD on the T7, V_ref on an ADS1115 (I²C)
C     = R_known · (V_ref / V_RTD)|known     one-time cross-calibration (Stage 2)
```

`C` folds in R_ref's value and the T7/ADS gain ratio, so the CRD current cancels
and only **stability** (R_ref tempco + relative ADC gain tempco) limits accuracy.

## Layout

```
host/                         # reusable acquisition library (the real measurement code)
├── config.py                 # electrical params + T7 (V_RTD) and ADS1115 (V_ref) maps
├── rtd.py                    # Callendar–Van Dusen R<->T (Pt100/Pt1000)
├── transport.py              # one device (T7): analog + I²C; LJM + I²C-level mock
├── t7_rtd.py                 # T7 driver: V_RTD on the differential pairs
├── ads1115.py                # ADS1115 driver: V_ref over I²C (register protocol)
├── acquire.py                # BoardSession: the time-aligned dual-ADC read
├── measurement.py            # ratiometric + cross-calibration math
├── calibration.py            # persist/load per-channel C (cross_cal.json)
└── paths.py                  # repo-relative locations

test/
├── bench/                    # harness around host/
│   ├── datalog.py            # CSV + meta-JSON logging, one stable schema
│   ├── stats.py              # noise, position-independence, baseline compare
│   ├── report.py             # TESTING_PLAN report skeleton -> reports/test/
│   ├── baseline_gen.py       # synthetic old-series-chain data (placeholder)
│   └── common.py             # shared CLI, gates, board build, operator prompts
├── procedures/               # stage0_*.py … stage8_*.py + run_all.py
├── tests/test_dryrun.py      # hardware-free self-test (mock, all stages)
└── data/                     # committed measured data + baselines/
```

## Install

```bash
python -m pip install -r test/requirements.txt   # numpy (dry run); labjack-ljm (bench)
```

Only `numpy` is needed for the mock/dry-run path. The real-T7 path also needs the
LabJack **LJM runtime** plus `labjack-ljm`.

## Dry run (no hardware)

```bash
# one stage (run from the test/ directory)
python procedures/stage2_cross_cal.py --mock --out-dir /tmp/scratch --report-dir /tmp/scratch

# whole sequence, fast
python procedures/run_all.py --mock --yes --samples 32 --out-dir /tmp/scratch --report-dir /tmp/scratch

# self-test (asserts host math + every stage run clean against the mock)
python tests/test_dryrun.py
```

`--mock` (default) uses the simulated board + T7 + ADS1115; `--yes` auto-confirms
the manual operator checks. Send synthetic output to a scratch dir so it isn't
committed (see `data/README.md`).

## On the bench

```bash
python procedures/run_all.py --real --identifier ANY        # full sequence, prompts the operator
python procedures/stage5_noise_position.py --real --samples 600 --navg 16
```

Drop `--mock`, add `--real`. The single LJM device reads V_RTD on its analog
pairs and drives the ADS1115 I²C bus on its digital lines. The operator is
prompted for physical checks and instrument entries; results and data land in
`reports/test/` and `test/data/`.

## Configuration & parameterization

All electrical parameters live in `host/config.py`. Override per run:

| Flag | Meaning | Default |
|------|---------|---------|
| `--rtd {Pt100,Pt1000}` | RTD type (sets R0, default T7 range) | Pt100 |
| `--channels N` | channel count (1–7; ceil(N/2) ADS1115 chips) | 3 |
| `--current-ua` | nominal CRD current (µA) | 220 |
| `--rref` | reference resistor (Ω) | 820 |
| `--t7-range` | T7 AIN ± range (V) | 0.1 (Pt100) / 1.0 (Pt1000) |
| `--resolution-index`, `--settling-us` | T7 acquisition (guards mux settling) | 12, 0 |
| `--navg` | T7 scans averaged per V_RTD read | 8 |
| `--ads-range` | ADS1115 PGA ± full-scale (V) | 0.256 |
| `--ads-rate`, `--ads-navg` | ADS1115 data rate (SPS) / conversions averaged | 128, 16 |
| `--samples`, `--interval-s` | record length / pacing | 64, 0 |

## Stage map (TESTING_PLAN Part 2)

| Stage | Script | Gate |
|------:|--------|------|
| 0 | `stage0_poweroff_checks.py` | no shorts / bridges (incl. I²C bus), power off |
| 1 | `stage1_power_i2c.py` | clean rail; **all ADS1115 present on I²C**; V_ref sane |
| 2 | `stage2_cross_cal.py` | per-channel C stable → **writes `cross_cal.json`** |
| 3 | `stage3_ratiometric.py` | recovered R = C·V_RTD/V_ref matches substituted R |
| 4 | `stage4_real_rtd.py` | two reference points within budget |
| 5 | `stage5_noise_position.py` | **noise ≤ floor AND position-independent** (headline) |
| 6 | `stage6_crosstalk.py` | perturbing one channel doesn't move the others |
| 7 | `stage7_thermal_soak.py` | **C drift** within budget (R_ref + rel. gain tempco) |
| 8 | `stage8_crd_noise.py` | CRD fractional current noise below the floor |

### The headline test (Stage 5)

The redesign exists to pass Stage 5: per-channel noise at/below the floor and
**no dependence on channel/position** (the old series chain's failure mode).
Stage 5 loads the old series-chain dataset (`--baseline`) and compares directly.
The committed `data/baselines/example_series_chain.csv` is a synthetic
placeholder; replace it with the real old-board log.

## Data schema

CSV columns (`bench/datalog.py:SCHEMA`): `iso_time, t_rel_s, stage, channel,
ads_addr, v_ref, v_rtd, ratio, c_const, r_calc, t_calc, r_known, note`. Each run
also writes a `.meta.json` with config, device info and conditions. Stable across
stages and versions so analysis code and old runs always load.

## Coordination

Track C owns `host/**` and `test/**` (and writes generated reports to
`reports/test/`). Independent of the schematic/layout work; on branch `trackC`.
Log: `docs/sessions/trackC.md`.