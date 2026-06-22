#!/usr/bin/env python3
"""Hardware-free self-test for the Track C bench tooling.

Runs every stage against the mock backend and checks the math, so the procedures
are proven import/lint-clean and runnable before any hardware exists. Pytest-
discoverable (test_* functions) and also runnable directly:

    python tests/test_dryrun.py
"""

import sys
import tempfile
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from config.board_config import (  # noqa: E402
    MODE_CAL_CURRENT,
    Q_VREF,
    Q_VRTD,
    make_config,
)
from lib.baseline_gen import generate_series_chain_baseline  # noqa: E402
from lib.measurement import compute_channel  # noqa: E402
from lib.rtd import resistance_from_temp, temp_from_resistance  # noqa: E402
from lib.stats import position_independence  # noqa: E402
from t7.board import BoardSession  # noqa: E402
from t7.mock_backend import MockT7Backend, make_scenario  # noqa: E402
from procedures import (  # noqa: E402
    run_all,
    stage2_current_cal,
    stage6_noise_position,
)


def _scratch() -> str:
    return tempfile.mkdtemp(prefix="trackc_")


def _base_args(out: str):
    return ["--mock", "--yes", "--out-dir", out, "--report-dir", out]


# ---- unit-level checks ---------------------------------------------------
def test_rtd_roundtrip():
    """R(T) and its inverse agree across the operating band, both RTD types."""
    for r0 in (100.0, 1000.0):
        for t in (-50.0, -20.0, 0.0, 25.0, 100.0, 150.0):
            r = resistance_from_temp(t, r0)
            assert abs(temp_from_resistance(r, r0) - t) < 1e-3, (r0, t)


def test_ratiometric_recovers_known_r():
    """Mock board -> ratiometric recovery returns the substituted resistance."""
    cfg = make_config("Pt100", 3)
    backend = MockT7Backend(config=cfg, scenario=make_scenario(cfg, seed=3), seed=3)
    board = BoardSession(backend, cfg)
    board.configure_inputs()
    r_known = resistance_from_temp(42.0, cfg.r0_ohms)
    for ch in cfg.channels:
        backend.scenario[ch].r_rtd_ohms = r_known
    volts = board.read_voltages(n_avg=64)
    for ch in cfg.channels:
        res = compute_channel(cfg, ch, volts[ch])
        assert Q_VREF in volts[ch] and Q_VRTD in volts[ch]
        assert abs(res.r_calc - r_known) / r_known < 2e-3, (ch, res.r_calc, r_known)


def test_position_independence_flags_growth():
    """The position-independence verdict catches noise growing up the chain."""
    good = position_independence({0: 1.0e-3, 1: 1.05e-3, 2: 0.98e-3})
    bad = position_independence({0: 1.0e-3, 1: 3.0e-3, 2: 6.0e-3})
    assert good.passed and not bad.passed


# ---- stage-level dry runs ------------------------------------------------
def test_full_sequence_pt100():
    out = _scratch()
    rc = run_all.main(_base_args(out) + ["--samples", "96"])
    assert rc == 0, "Pt100 full-diff sequence should pass against the nominal mock"


def test_full_sequence_pt1000():
    out = _scratch()
    rc = run_all.main(_base_args(out) + ["--rtd", "Pt1000", "--samples", "64"])
    assert rc == 0, "Pt1000 sequence should pass (parameterization, no rewrite)"


def test_calibrated_current_mode_7ch():
    """Density mode: Stage 2 calibration then Stage 6, 7 channels, Pt1000."""
    out = _scratch()
    args = [
        "--mock", "--yes", "--mode", MODE_CAL_CURRENT, "--rtd", "Pt1000",
        "--channels", "7", "--out-dir", out, "--report-dir", out,
    ]
    assert stage2_current_cal.main(args) == 0
    cfg = make_config("Pt1000", 7, measurement_mode=MODE_CAL_CURRENT)
    base = generate_series_chain_baseline(
        cfg, out_dir=pathlib.Path(out), filename="bl.csv", n_samples=64
    )
    rc = stage6_noise_position.main(args + ["--samples", "160", "--baseline", str(base)])
    assert rc == 0


def test_stage6_detects_series_chain():
    """A position-dependent (series-chain) board must FAIL the Stage-6 gate."""
    out = _scratch()
    stage2_current_cal.main(_base_args(out))
    rc = stage6_noise_position.main(
        _base_args(out) + ["--scenario", "series_chain", "--samples", "160"]
    )
    assert rc == 1, "Stage 6 must fail on a series-chain (position-dependent) board"


_TESTS = [
    test_rtd_roundtrip,
    test_ratiometric_recovers_known_r,
    test_position_independence_flags_growth,
    test_full_sequence_pt100,
    test_full_sequence_pt1000,
    test_calibrated_current_mode_7ch,
    test_stage6_detects_series_chain,
]


def main() -> int:
    failures = 0
    for fn in _TESTS:
        try:
            fn()
        except AssertionError as exc:  # noqa: PERF203
            failures += 1
            print(f"FAIL  {fn.__name__}: {exc}")
        except Exception as exc:  # pragma: no cover - surface unexpected errors
            failures += 1
            print(f"ERROR {fn.__name__}: {type(exc).__name__}: {exc}")
        else:
            print(f"ok    {fn.__name__}")
    print(f"\n{len(_TESTS) - failures}/{len(_TESTS)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())