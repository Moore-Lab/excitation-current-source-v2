# test/data — committed bench measurements

Raw measured data is **irreplaceable and committed** (DIRECTORY_MANAGEMENT.md).
Each stage run writes a CSV plus a `.meta.json` provenance sidecar here:

| File | Written by | Contents |
|------|-----------|----------|
| `stage1_bringup_<runid>.csv` | Stage 1 | I²C scan + raw V_ref / V_RTD |
| `cross_cal.json` | Stage 2 | per-channel cross-cal constant **C** |
| `stage2_crosscal_<runid>.csv` | Stage 2 | cross-cal measurements (C repeats) |
| `stage3_ratiometric_<runid>.csv` | Stage 3 | substitution accuracy sweep |
| `stage4_real_rtd_<runid>.csv` | Stage 4 | two-point real-RTD readings |
| `stage5_noise_<runid>.csv` | Stage 5 | noise / position-independence record |
| `stage6_crosstalk_<runid>.csv` | Stage 6 | aggressor/victim shifts |
| `stage7_soak_<runid>.csv` | Stage 7 | thermal soak / C-drift log |
| `stage8_crd_noise_<runid>.csv` | Stage 8 | per-sample V_ref (CRD noise) |
| `baselines/` | reference | old series-chain datasets for the Stage 5 comparison |

All CSVs share one schema (see `bench/datalog.py:SCHEMA`) so any reader / old run
loads the same way.

## Commit policy
- **Real bench data:** commit it.
- **Synthetic `--mock` dry-run output:** do **not** commit. Point a dry run at a
  scratch dir: `--out-dir /tmp/scratch --report-dir /tmp/scratch`.
- `baselines/example_series_chain.csv` is a **synthetic placeholder** (generated
  by `bench/baseline_gen.py`) so the Stage 5 comparison tool is testable before
  the real old-board data exists. Replace it with Lucas's actual series-chain log
  and point Stage 5 at it via `--baseline`.