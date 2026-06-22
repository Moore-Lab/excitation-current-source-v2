"""Generate a synthetic 'old series-chain board' dataset for Stage 6 to compare against.

The REAL baseline is Lucas's logged data from the old series-chain rig; drop it
in ``test/data/baselines/`` and point Stage 6 at it with ``--baseline``. This
generator only fabricates a clearly-synthetic placeholder (noise growing up the
chain) so the comparison tooling is exercised before that data exists.

Run as a module to (re)create the committed example:
    python -m lib.baseline_gen
"""

from __future__ import annotations

from pathlib import Path

from config.board_config import BoardConfig, DEFAULT_CONFIG, Q_VRTD
from lib.datalog import Recorder
from lib.measurement import compute_channel
from lib.paths import BASELINE_DIR, ensure_dir
from t7.board import BoardSession
from t7.mock_backend import MockT7Backend, series_chain_scenario


def generate_series_chain_baseline(
    config: BoardConfig = DEFAULT_CONFIG,
    n_samples: int = 64,
    seed: int = 7,
    out_dir: Path = BASELINE_DIR,
    filename: str = "example_series_chain.csv",
) -> Path:
    """Log a synthetic series-chain run and return the CSV path."""
    ensure_dir(out_dir)
    scenario = series_chain_scenario(config, seed=seed)
    backend = MockT7Backend(config=config, scenario=scenario, seed=seed)
    board = BoardSession(backend, config)
    board.configure_inputs()

    # Fixed run id so the example file path is stable / overwritable.
    # synthetic calibration (nominal current) so the writer works in any mode,
    # including calibrated-current, without a Stage-2 file.
    calib = {ch: config.excitation_current_a for ch in config.channels}

    rec = Recorder(
        "baseline_series_chain", config, out_dir=out_dir, run_id="example",
        device_info={"backend": "mock", "note": "SYNTHETIC series-chain placeholder"},
        conditions="synthetic old-board data; noise grows up the channel index",
    )
    try:
        for _ in range(n_samples):
            volts = board.read_voltages(n_avg=1)
            for ch in config.channels:
                res = compute_channel(config, ch, volts[ch], i_cal_a=calib[ch])
                rec.log(ch, v_rtd=volts[ch][Q_VRTD], r_calc=res.r_calc, t_calc=res.t_calc,
                        note="synthetic series-chain")
    finally:
        rec.close()

    # Recorder names files <stage>_<run_id>.csv; normalise to the requested name.
    produced = out_dir / "baseline_series_chain_example.csv"
    target = out_dir / filename
    if produced.exists():
        produced.replace(target)
        meta = out_dir / "baseline_series_chain_example.meta.json"
        if meta.exists():
            meta.replace(out_dir / (Path(filename).stem + ".meta.json"))
    return target


if __name__ == "__main__":
    p = generate_series_chain_baseline()
    print(f"wrote synthetic baseline: {p}")
