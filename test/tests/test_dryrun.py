#!/usr/bin/env python3
"""Hardware-free self-test for the Track C acquisition + bench tooling.

Exercises the host/ library and every stage against the mock transport so the
code is proven import/lint-clean and runnable before any hardware exists. The
mock models the ADS1115 at the I²C-register level, so the real driver's register
packing/unpacking is exercised here -- not bypassed. Pytest-discoverable and also
runnable directly:

    python tests/test_dryrun.py
"""

import sys
import tempfile
import pathlib

_T = pathlib.Path(__file__).resolve()
sys.path[:0] = [str(_T.parents[1]), str(_T.parents[2])]  # test/, repo root

from bench.baseline_gen import generate_series_chain_baseline  # noqa: E402
from bench.stats import position_independence  # noqa: E402
from host.acquire import BoardSession  # noqa: E402
from host.config import Q_VREF, Q_VRTD, make_config  # noqa: E402
from host.measurement import compute_channel, cross_cal_constant  # noqa: E402
from host.rtd import resistance_from_temp, temp_from_resistance  # noqa: E402
from host.transport import MockTransport, make_scenario  # noqa: E402
from procedures import (  # noqa: E402
    run_all,
    stage5_noise_position,
    stage8_crd_noise,
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


def test_i2c_scan_finds_expected_chips():
    """The I²C scan returns exactly the addresses the channel count implies."""
    for n, expect in ((3, [0x48, 0x49]), (1, [0x48]), (7, [0x48, 0x49, 0x4A, 0x4B])):
        cfg = make_config("Pt100", n)
        board = BoardSession(MockTransport(config=cfg, scenario=make_scenario(cfg)), cfg)
        board.configure()
        assert board.scan_i2c() == expect, (n, board.scan_i2c())


def test_cross_cal_recovers_known_r():
    """Mock board -> cross-cal C -> ratiometric recovery returns the substituted R."""
    cfg = make_config("Pt100", 3)
    sc = make_scenario(cfg, seed=3)
    board = BoardSession(MockTransport(config=cfg, scenario=sc, seed=3), cfg)
    board.configure()
    # cross-calibrate at one resistance
    r_cal = 110.0
    for ch in cfg.channels:
        sc[ch].r_rtd_ohms = r_cal
    constants = {}
    for ch in cfg.channels:
        v = board.read_channel(ch, t7_navg=16, ads_navg=16)
        constants[ch] = cross_cal_constant(r_cal, v[Q_VRTD], v[Q_VREF])
    # recover a different resistance
    r_test = resistance_from_temp(70.0, cfg.r0_ohms)
    for ch in cfg.channels:
        sc[ch].r_rtd_ohms = r_test
    for ch in cfg.channels:
        v = board.read_channel(ch, t7_navg=16, ads_navg=16)
        res = compute_channel(cfg, ch, v, constants[ch])
        assert Q_VREF in v and Q_VRTD in v
        assert abs(res.r_calc - r_test) / r_test < 2e-3, (ch, res.r_calc, r_test)


def test_current_value_cancels_in_ratio():
    """The whole point: the CRD current value drops out of the recovered R."""
    cfg = make_config("Pt100", 1)
    sc = make_scenario(cfg, seed=5)
    sc[0].r_rtd_ohms = 120.0
    board = BoardSession(MockTransport(config=cfg, scenario=sc, seed=5), cfg)
    board.configure()
    v = board.read_channel(0, t7_navg=64, ads_navg=64)
    C = cross_cal_constant(120.0, v[Q_VRTD], v[Q_VREF])
    # change the current by 30 %; recovered R must not move
    sc[0].current_a *= 1.3
    v2 = board.read_channel(0, t7_navg=64, ads_navg=64)
    r = compute_channel(cfg, 0, v2, C).r_calc
    assert abs(r - 120.0) / 120.0 < 2e-3, r


def test_position_independence_flags_growth():
    """The position-independence verdict catches noise growing up the chain."""
    good = position_independence({0: 1.0e-3, 1: 1.05e-3, 2: 0.98e-3})
    bad = position_independence({0: 1.0e-3, 1: 3.0e-3, 2: 6.0e-3})
    assert good.passed and not bad.passed


# ---- stage-level dry runs ------------------------------------------------
def test_full_sequence_pt100():
    out = _scratch()
    rc = run_all.main(_base_args(out) + ["--samples", "48", "--ads-navg", "8"])
    assert rc == 0, "Pt100 full sequence should pass against the nominal mock"


def test_full_sequence_pt1000():
    out = _scratch()
    rc = run_all.main(_base_args(out) + ["--rtd", "Pt1000", "--samples", "40", "--ads-navg", "8"])
    assert rc == 0, "Pt1000 sequence should pass (parameterization, no rewrite)"


def test_seven_channel_sequence():
    """Scalability: a fully populated 7-channel board (4 ADS1115) runs clean."""
    out = _scratch()
    # The headline position-independence verdict needs an adequate record: with 7
    # channels the std-of-std estimator spreads at low sample counts (a finite-n
    # artifact, not real position dependence), so use a longer record as on the bench.
    rc = run_all.main(_base_args(out) + ["--channels", "7", "--samples", "320", "--ads-navg", "8"])
    assert rc == 0, "7-channel sequence should pass (ceil(7/2)=4 ADS1115)"


def test_stage5_detects_series_chain():
    """A position-dependent (series-chain) board must FAIL the Stage-5 gate."""
    out = _scratch()
    rc = stage5_noise_position.main(
        _base_args(out) + ["--scenario", "series_chain", "--samples", "160", "--ads-navg", "8"]
    )
    assert rc == 1, "Stage 5 must fail on a series-chain (position-dependent) board"


def test_stage8_detects_noisy_crd():
    """An excessively noisy CRD must FAIL the Stage-8 gate."""
    out = _scratch()
    rc = stage8_crd_noise.main(
        _base_args(out) + ["--samples", "128", "--crd-noise-ppm", "3000"]
    )
    assert rc == 1, "Stage 8 must fail when CRD current noise is well above the floor"


def test_baseline_generator():
    """The synthetic series-chain baseline generates and loads with the schema."""
    out = pathlib.Path(_scratch())
    cfg = make_config("Pt100", 3)
    p = generate_series_chain_baseline(cfg, out_dir=out, filename="bl.csv", n_samples=32)
    assert p.exists() and (out / "bl.meta.json").exists()


_TESTS = [
    test_rtd_roundtrip,
    test_i2c_scan_finds_expected_chips,
    test_cross_cal_recovers_known_r,
    test_current_value_cancels_in_ratio,
    test_position_independence_flags_growth,
    test_full_sequence_pt100,
    test_full_sequence_pt1000,
    test_seven_channel_sequence,
    test_stage5_detects_series_chain,
    test_stage8_detects_noisy_crd,
    test_baseline_generator,
]


def main() -> int:
    failures = 0
    for fn in _TESTS:
        try:
            fn()
        except AssertionError as exc:
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