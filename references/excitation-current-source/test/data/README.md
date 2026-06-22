# test/data — committed bench measurements

Raw measured data is **irreplaceable and committed** (DIRECTORY_MANAGEMENT.md).
Each stage run writes a CSV plus a `.meta.json` provenance sidecar here:

| File | Written by | Contents |
|------|-----------|----------|
| `stage2_current_<runid>.csv` | Stage 2 | per-channel measured current |
| `calibration.json` | Stage 2 | per-channel current constants (calibrated-current mode) |
| `stage3_ratiometric_<runid>.csv` | Stage 3 | substitution accuracy sweep |
| `stage5_real_rtd_<runid>.csv` | Stage 5 | two-point real-RTD readings |
| `stage6_noise_<runid>.csv` | Stage 6 | noise / position-independence record |
| `stage7_crosstalk_<runid>.csv` | Stage 7 | victim/aggressor shifts |
| `stage8_soak_<runid>.csv` | Stage 8 | thermal soak / drift log |
| `baselines/` | reference | old series-chain datasets for the Stage 6 comparison |

All CSVs share one schema (see `lib/datalog.py:SCHEMA`) so any reader / old run
loads the same way.

## Commit policy
- **Real bench data:** commit it.
- **Synthetic `--mock` dry-run output:** do **not** commit. Point a dry run at a
  scratch dir: `--out-dir /tmp/scratch --report-dir /tmp/scratch`.
- `baselines/example_series_chain.csv` is a **synthetic placeholder** (generated
  by `lib/baseline_gen.py`) so the Stage 6 comparison tool is testable before the
  real old-board data exists. Replace it with Lucas's actual series-chain log and
  point Stage 6 at it via `--baseline`.