#!/usr/bin/env python3
"""Stage 8 — Thermal soak / drift (TESTING_PLAN Part 2).

Log all channels for an extended period at a fixed temperature. Gate: drift
within budget, and confirm the reference-resistor tempco is the dominant drift
term as predicted (not the REF200, not grounding) -- board_spec.md sec.3.
"""

import sys
import time
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from config.board_config import Q_VRTD  # noqa: E402
from lib.calibration import try_load_calibration  # noqa: E402
from lib.datalog import Recorder  # noqa: E402
from lib.measurement import compute_channel  # noqa: E402
from lib.report import StageReport, markdown_table  # noqa: E402
from lib.rtd import resistance_from_temp  # noqa: E402
from lib.stats import noise_stats  # noqa: E402
from procedures import common  # noqa: E402

DEFAULT_DRIFT_BUDGET_C = 0.1   # allowed end-to-end drift over the soak


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 8 — thermal soak / drift")
    parser.add_argument("--drift-budget-c", type=float, default=DEFAULT_DRIFT_BUDGET_C)
    parser.add_argument("--soak-temp", type=float, default=25.0)
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 8 — THERMAL SOAK / DRIFT", config, args)

    backend, board = common.make_board(args, config)
    board.configure_inputs()
    calib = try_load_calibration(args.out_dir / "calibration.json")
    common.set_mock_rtd(board, resistance_from_temp(args.soak_temp, config.r0_ohms))
    common.confirm(f"hold all channels at a fixed {args.soak_temp:g} C for the soak", args)

    t_series = {ch: [] for ch in config.channels}
    with backend, Recorder("stage8_soak", config, out_dir=args.out_dir,
                           device_info=board.device_info(),
                           conditions=f"soak at {args.soak_temp:g} C, {args.samples} samples"
                                      f" @ {args.interval_s:g}s") as rec:
        for i in range(args.samples):
            volts = board.read_voltages(n_avg=args.navg)
            for ch in config.channels:
                i_cal = calib.get(ch) if calib else None
                res = compute_channel(config, ch, volts[ch], i_cal_a=i_cal)
                rec.log(ch, v_rtd=volts[ch][Q_VRTD], r_calc=res.r_calc, t_calc=res.t_calc,
                        note="soak sample")
                t_series[ch].append(res.t_calc)
            if args.interval_s > 0 and i < args.samples - 1:
                time.sleep(args.interval_s)

    gate = common.GateLog("Stage 8 — thermal soak / drift")
    rows = []
    for ch in config.channels:
        st = noise_stats(np.array(t_series[ch]))
        ok = abs(st.drift) <= args.drift_budget_c
        gate.record(f"ch{ch} drift within budget", ok,
                    f"drift {st.drift*1e3:+.2f} mK <= {args.drift_budget_c*1e3:g} mK")
        rows.append([ch, f"{st.drift*1e3:+.2f}", f"{st.std*1e3:.2f}", f"{st.mean:.3f}"])

    tempco_ok = common.confirm(
        "R_ref tempco is the dominant drift term as predicted (board stable to a few C)", args
    )
    gate.record("R_ref tempco dominates (per prediction)", tempco_ok)

    report = StageReport(
        stage_name="Stage 8 — Thermal soak / drift",
        objective=(
            "Confirm long-term drift is within budget and dominated by the R_ref "
            "tempco, not the REF200 or grounding (TESTING_PLAN Part 2)."
        ),
        setup=f"Fixed temperature soak. {config.summary()}. "
              f"{args.samples} samples @ {args.interval_s:g}s.",
        method="Log every channel over the soak; fit end-to-end drift; gate against budget.",
        results_intro=f"Drift budget +/-{args.drift_budget_c*1e3:g} mK over the record.",
        results_table=markdown_table(
            ["Ch", "Drift [mK]", "Noise std [mK]", "Mean [C]"], rows
        ),
        passed=gate.passed,
        criterion=f"|drift| <= {args.drift_budget_c*1e3:g} mK per channel; R_ref tempco dominant.",
        margin="drift within budget" if gate.passed else "drift exceeds budget",
        next_action="Bring-up complete; archive data and compare against SPICE predictions.",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())