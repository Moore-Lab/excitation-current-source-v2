# Bench bring-up & T7 control (Track C)

Runnable, staged bring-up procedures and the LabJack T7 Pro control / data-logging
code for the REF200 RTD board. The moment the physical board exists, Lucas can run
the staged tests with no glue work left to do. Everything here runs **with no
hardware** against a mock backend, so the procedures are written, linted, and
dry-run-verified ahead of fab.

Maps to `docs/TESTING_PLAN.md` Part 2 (Stages 0–8) and uses the shared report
skeleton. Parameterized for **Pt100 and Pt1000** (and 3 measurement modes) so the
RTD-type decision never requires a rewrite. Default config = the resolved design
point (Pt100, 3 ch, 100 µA, R_ref 100 Ω, full-differential, ±0.1 V).

## Layout

```
test/
├── config/board_config.py   # electrical params + T7 AIN map (parameterized)
├── lib/
│   ├── rtd.py               # Callendar–Van Dusen R<->T (Pt100/Pt1000)
│   ├── measurement.py       # ratiometric & calibrated-current recovery
│   ├── calibration.py       # per-channel current constants (Stage 2 I/O)
│   ├── datalog.py           # CSV + meta-JSON logging, one stable schema
│   ├── stats.py             # noise, position-independence, baseline compare
│   ├── report.py            # TESTING_PLAN report skeleton -> reports/test/
│   ├── baseline_gen.py      # synthetic old-series-chain data (placeholder)
│   └── paths.py             # repo-relative locations
├── t7/
│   ├── backend.py           # abstract T7 interface + factory
│   ├── ljm_backend.py       # real T7 over LJM (bench only)
│   ├── mock_backend.py      # hardware-free board+T7 simulation
│   └── board.py             # AIN config + per-channel voltage reads
├── procedures/
│   ├── common.py            # shared CLI, gates, operator prompts
│   ├── stage0_poweroff_checks.py ... stage8_thermal_soak.py
│   └── run_all.py           # run Stage 0 -> 8 in order
├── tests/test_dryrun.py     # hardware-free self-test (mock, all stages)
└── data/                    # committed measured data + baselines/
```

## Install

```bash
python -m pip install -r test/requirements.txt   # numpy (dry run); labjack-ljm (bench)
```

Only `numpy` is needed for the mock/dry-run path. The real-T7 path also needs the
LabJack **LJM runtime** plus `labjack-ljm` (see `requirements.txt`).

## Dry run (no hardware)

From the `test/` directory:

```bash
# one stage
python procedures/stage2_current_cal.py --mock --out-dir /tmp/scratch --report-dir /tmp/scratch

# whole sequence, fast
python procedures/run_all.py --mock --yes --samples 16 --out-dir /tmp/scratch --report-dir /tmp/scratch

# self-test (asserts every stage runs clean against the mock)
python tests/test_dryrun.py
```

`--mock` (default) uses the simulated board+T7; `--yes` auto-confirms the manual
operator checks. Send synthetic output to a scratch dir so it isn't committed.

## On the bench

```bash
python procedures/run_all.py --real --identifier ANY        # full sequence, prompts the operator
python procedures/stage6_noise_position.py --real --samples 600 --navg 16
```

Drop `--mock`, add `--real`. The operator is prompted for the physical checks and
DMM/scope entries; results and data land in `reports/test/` and `test/data/`.

## Configuration & parameterization

All electrical parameters live in `config/board_config.py`. Override per run:

| Flag | Meaning | Default |
|------|---------|---------|
| `--rtd {Pt100,Pt1000}` | RTD type (sets R0, default I / R_ref / range) | Pt100 |
| `--channels N` | channel count | 3 |
| `--mode` | `full_differential` / `single_ended_subtract` / `calibrated_current` | full_differential |
| `--current-ua` | excitation current (µA) | 100 |
| `--rref` | reference resistor (Ω) | 100 (Pt100) / 1000 (Pt1000) |
| `--range` | T7 AIN ± range (V) | 0.1 (Pt100) / 1.0 (Pt1000) |
| `--resolution-index`, `--settling-us` | T7 acquisition (guards mux settling) | 8, 0 |
| `--navg`, `--samples`, `--interval-s` | averaging / record length / pacing | 8, 64, 0 |

The three measurement modes follow `board_spec.md` §5; the AIN map is generated
per mode (full-diff: 4 AIN/ch, max 3; SE-subtract: 3 AIN/ch, max 4;
calibrated-current: 2 AIN/ch, max 7). The stage scripts and the measurement math
don't branch on mode — `BoardSession.read_voltages()` collapses all three to
`{V_ref, V_RTD}`.

## Stage map (TESTING_PLAN Part 2)

| Stage | Script | Gate |
|------:|--------|------|
| 0 | `stage0_poweroff_checks.py` | no shorts / bridges (power off) |
| 1 | `stage1_power_tree.py` | clean rail, low ripple |
| 2 | `stage2_current_cal.py` | each channel current in spec → **writes `calibration.json`** |
| 3 | `stage3_ratiometric.py` | recovered R matches substituted precision R |
| 4 | `stage4_compliance.py` | source ≥ 2.5 V at max RTD R |
| 5 | `stage5_real_rtd.py` | two reference points within budget; Kelvin confirmed |
| 6 | `stage6_noise_position.py` | **noise ≤ floor AND position-independent** (headline) |
| 7 | `stage7_crosstalk.py` | no cross-coupling between channels |
| 8 | `stage8_thermal_soak.py` | drift within budget; R_ref tempco dominates |

### The headline test (Stage 6)

The whole redesign exists to pass Stage 6: per-channel noise at/below the T7 +
Johnson floor, and **no dependence on channel/position** (the old series chain's
failure mode). Stage 6 loads the old series-chain dataset (`--baseline`) and
compares directly — new vs old per-channel noise and spread. The committed
`data/baselines/example_series_chain.csv` is a synthetic placeholder; replace it
with the real old-board log.

## Data schema

CSV columns (`lib/datalog.py:SCHEMA`): `iso_time, t_rel_s, stage, channel, v_ref,
v_rtd, r_calc, t_calc, r_known, i_meas_a, note`. Each run also writes a
`.meta.json` with the config, T7 info, and conditions. Stable across stages and
versions so analysis code and old runs always load.

## Coordination
Track C owns `test/**` (and writes generated reports to `reports/test/`). It is
independent of the schematic/layout work; on branch `trackC`. Log:
`docs/sessions/trackC.md`.
