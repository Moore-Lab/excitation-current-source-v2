"""Generate a synthetic 'old series-chain board' dataset for Stage 5 to compare against.

The REAL baseline is Lucas's logged data from the old series-chain rig; drop it
in ``test/data/baselines/`` and point Stage 5 at it with ``--baseline``. This
generator only fabricates a clearly-synthetic placeholder (noise growing up the
chain) so the comparison tooling is exercised before that data exists.

Run as a module to (re)create the committed example:
    python -m bench.baseline_gen
"""

from __future__ import annotations

import sys
import pathlib
from pathlib import Path

_T = pathlib.Path(__file__).resolve()
sys.path[:0] = [str(_T.parents[1]), str(_T.parents[2])]  # test/, repo root

from host.acquire import BoardSession  # noqa: E402
from host.config import BoardConfig, DEFAULT_CONFIG, Q_VREF, Q_VRTD  # noqa: E402
from host.measurement import compute_channel  # noqa: E402
from host.paths import BASELINE_DIR, ensure_dir  # noqa: E402
from host.transport import MockTransport, series_chain_scenario  # noqa: E402

from bench.datalog import Recorder  # noqa: E402


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
    transport = MockTransport(config=config, scenario=scenario, seed=seed)
    board = BoardSession(transport, config)
    board.configure()

    # Synthetic per-channel C (ideal gain ratio -> C == R_ref). The point of the
    # baseline is the *noise* profile growing up the chain, not its calibration.
    constants = {ch: config.r_ref_ohms for ch in config.channels}

    rec = Recorder(
        "baseline_series_chain", config, out_dir=out_dir, run_id="example",
        device_info={"backend": "mock", "note": "SYNTHETIC series-chain placeholder"},
        conditions="synthetic old-board data; noise grows up the channel index",
    )
    try:
        for _ in range(n_samples):
            volts = board.read_channels(t7_navg=1)
            for ch in config.channels:
                res = compute_channel(config, ch, volts[ch], constants[ch])
                rec.log(ch, ads_addr=config.ads_map[ch].addr_hex,
                        v_ref=volts[ch][Q_VREF], v_rtd=volts[ch][Q_VRTD],
                        ratio=res.ratio, c_const=res.c_const,
                        r_calc=res.r_calc, t_calc=res.t_calc,
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
