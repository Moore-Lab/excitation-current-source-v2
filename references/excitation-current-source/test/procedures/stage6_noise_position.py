#!/usr/bin/env python3
"""Stage 6 — Noise & position independence (TESTING_PLAN Part 2, headline test).

At a fixed, stable temperature, record noise on every channel and check:
  (a) per-channel noise at/below the T7 + Johnson floor, and
  (b) NO dependence on channel/position -- the failure mode of the old series
      chain. Directly compares against the old series-chain baseline where noise
      grew up the chain.

This is the test the whole redesign exists to pass.
"""

import sys
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from config.board_config import Q_VRTD  # noqa: E402
from lib.calibration import try_load_calibration  # noqa: E402
from lib.datalog import Recorder, channel_series  # noqa: E402
from lib.measurement import compute_channel  # noqa: E402
from lib.paths import BASELINE_DIR  # noqa: E402
from lib.report import StageReport, markdown_table  # noqa: E402
from lib.rtd import resistance_from_temp  # noqa: E402
from lib.stats import compare_to_baseline, noise_stats, position_independence  # noqa: E402
from procedures import common  # noqa: E402

DEFAULT_FLOOR_MK = 100.0      # per-channel temp-noise gate (milli-degC, rms)
DEFAULT_SPREAD_TOL = 1.5      # max/min channel-noise ratio for position-independence


def _baseline_std(path, config, calib):
    """Per-channel temperature-noise std from an old series-chain dataset."""
    if not path.exists():
        return None
    out = {}
    for ch in config.channels:
        t = channel_series(path, "t_calc", ch)
        if t.size:
            out[ch] = float(np.std(t, ddof=1)) if t.size > 1 else 0.0
    return out or None


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 6 — noise & position independence")
    parser.add_argument("--floor-mk", type=float, default=DEFAULT_FLOOR_MK,
                        help="per-channel temp-noise gate, milli-degC rms")
    parser.add_argument("--spread-tol", type=float, default=DEFAULT_SPREAD_TOL,
                        help="max/min channel-noise ratio for position independence")
    parser.add_argument("--soak-temp", type=float, default=0.0,
                        help="fixed temperature for the noise record (mock)")
    parser.add_argument("--baseline", type=pathlib.Path,
                        default=BASELINE_DIR / "example_series_chain.csv",
                        help="old series-chain dataset to compare against")
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 6 — NOISE & POSITION INDEPENDENCE", config, args)

    backend, board = common.make_board(args, config)
    board.configure_inputs()
    calib = try_load_calibration(args.out_dir / "calibration.json")
    common.set_mock_rtd(board, resistance_from_temp(args.soak_temp, config.r0_ohms))
    common.confirm(f"hold all channels at a fixed, stable temperature (~{args.soak_temp:g} C)", args)

    # collect N samples per channel
    t_series = {ch: [] for ch in config.channels}
    with backend, Recorder("stage6_noise", config, out_dir=args.out_dir,
                           device_info=board.device_info(),
                           conditions=f"fixed temp ~{args.soak_temp:g} C, {args.samples} samples") as rec:
        for _ in range(args.samples):
            volts = board.read_voltages(n_avg=args.navg)
            for ch in config.channels:
                i_cal = calib.get(ch) if calib else None
                res = compute_channel(config, ch, volts[ch], i_cal_a=i_cal)
                rec.log(ch, v_rtd=volts[ch][Q_VRTD], r_calc=res.r_calc, t_calc=res.t_calc,
                        note="noise sample")
                t_series[ch].append(res.t_calc)
        data_path = rec.csv_path

    # per-channel noise in temperature units
    per_ch_std = {}
    rows = []
    for ch in config.channels:
        st = noise_stats(np.array(t_series[ch]))
        per_ch_std[ch] = st.std
        rows.append([ch, f"{st.std*1e3:.2f}", f"{st.pp*1e3:.2f}", f"{st.mean:.3f}"])

    gate = common.GateLog("Stage 6 — noise & position independence")
    floor_c = args.floor_mk * 1e-3
    for ch in config.channels:
        gate.record(f"ch{ch} noise <= floor", per_ch_std[ch] <= floor_c,
                    f"{per_ch_std[ch]*1e3:.2f} mK <= {args.floor_mk:g} mK")

    pos = position_independence(per_ch_std, tolerance_ratio=args.spread_tol)
    gate.record("position independence", pos.passed,
                f"spread {pos.spread_ratio:.2f}x (tol {args.spread_tol:g}x)"
                + ("; " + "; ".join(pos.notes) if pos.notes else ""))

    # direct comparison to the old series-chain board
    cmp_table = "_No baseline dataset found; skipped comparison._"
    base_std = _baseline_std(args.baseline, config, calib)
    if base_std:
        cmp = compare_to_baseline(per_ch_std, base_std)
        crows = [
            [ch, f"{per_ch_std[ch]*1e3:.2f}", f"{base_std.get(ch, float('nan'))*1e3:.2f}",
             f"{cmp.improvement.get(ch, float('nan')):.2f}x"]
            for ch in config.channels
        ]
        cmp_table = markdown_table(
            ["Ch", "New noise [mK]", "Old (series) [mK]", "Improvement"], crows
        )
        cmp_table += (f"\n\nSpread (max/min): new {cmp.new_spread:.2f}x vs "
                      f"old series-chain {cmp.baseline_spread:.2f}x.")

    report = StageReport(
        stage_name="Stage 6 — Noise & position independence",
        objective=(
            "The headline acceptance test: per-channel noise at/below the floor and "
            "independent of channel position, vs the old series-chain board "
            "(TESTING_PLAN Part 2)."
        ),
        setup=f"All channels at a fixed stable temperature. {config.summary()}. "
              f"{args.samples} samples, navg={args.navg}. Data: `{data_path.name}`.",
        method=(
            "Record N readings per channel; compute per-channel temperature-noise "
            "std; test for position dependence; compare to the series-chain baseline."
        ),
        results_intro="Per-channel noise (temperature units):",
        results_table=markdown_table(
            ["Ch", "Noise std [mK]", "Noise pp [mK]", "Mean [C]"], rows
        ) + "\n\n### Comparison to old series-chain board\n\n" + cmp_table,
        passed=gate.passed,
        criterion=(
            f"(a) every channel <= {args.floor_mk:g} mK rms, and (b) noise spread "
            f"<= {args.spread_tol:g}x with no growth up the channel index."
        ),
        margin=f"spread {pos.spread_ratio:.2f}x" if gate.passed else "; ".join(pos.notes) or "floor exceeded",
        next_action="Proceed to Stage 7 (crosstalk).",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())