#!/usr/bin/env python3
"""Stage 5 — Real RTDs, two-point (TESTING_PLAN Part 2).

Connect the actual 4-wire RTDs. Take two known points (ice bath 0 degC -> R0, and
a second known temperature against a reference thermometer). Gate: both points
within budget, and Kelvin sensing confirmed (vary lead length -> no shift).
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from config.board_config import Q_VREF, Q_VRTD  # noqa: E402
from lib.calibration import try_load_calibration  # noqa: E402
from lib.datalog import Recorder  # noqa: E402
from lib.measurement import compute_channel  # noqa: E402
from lib.report import StageReport, markdown_table  # noqa: E402
from lib.rtd import resistance_from_temp  # noqa: E402
from procedures import common  # noqa: E402

DEFAULT_POINTS = [0.0, 100.0]   # ice bath + a second reference point
DEFAULT_BUDGET_C = 0.5          # degC acceptance vs the reference thermometer


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 5 — real RTDs, two-point")
    parser.add_argument("--points", default=None,
                        help="comma-separated reference temperatures (degC)")
    parser.add_argument("--budget-c", type=float, default=DEFAULT_BUDGET_C)
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 5 — REAL RTDs (TWO-POINT)", config, args)

    backend, board = common.make_board(args, config)
    board.configure_inputs()
    calib = try_load_calibration(args.out_dir / "calibration.json")
    points = [float(x) for x in args.points.split(",")] if args.points else DEFAULT_POINTS

    gate = common.GateLog("Stage 5 — real RTDs two-point")
    rows = []
    with backend, Recorder("stage5_real_rtd", config, out_dir=args.out_dir,
                           device_info=board.device_info(),
                           conditions="real 4-wire RTDs at reference temperatures") as rec:
        for t_ref in points:
            # mock: drive each RTD to its true resistance at the reference temp
            common.set_mock_rtd(board, resistance_from_temp(t_ref, config.r0_ohms))
            common.confirm(f"stabilise all RTDs at reference {t_ref:g} degC", args)
            t_meas_ref = common.ask_float(
                f"reference thermometer reading (degC) at point {t_ref:g}", args, auto_value=t_ref
            )
            volts = board.read_voltages(n_avg=args.navg)
            for ch in config.channels:
                i_cal = calib.get(ch) if calib else None
                res = compute_channel(config, ch, volts[ch], i_cal_a=i_cal)
                err_c = res.t_calc - t_meas_ref
                rec.log(ch, v_ref=volts[ch].get(Q_VREF, ""), v_rtd=volts[ch][Q_VRTD],
                        r_calc=res.r_calc, t_calc=res.t_calc, r_known="",
                        note=f"ref={t_meas_ref:.3f}C")
                ok = abs(err_c) <= args.budget_c
                gate.record(f"ch{ch} @ {t_ref:g}C within budget", ok,
                            f"T_calc={res.t_calc:.3f}C (err {err_c:+.3f}C)")
                rows.append([ch, f"{t_ref:g}", f"{res.r_calc:.4f}", f"{res.t_calc:.3f}",
                             f"{err_c:+.3f}"])

    kelvin_ok = common.confirm(
        "Kelvin confirmed: vary a sense lead length and reading does not shift", args
    )
    gate.record("Kelvin sensing confirmed (lead-length independent)", kelvin_ok)

    report = StageReport(
        stage_name="Stage 5 — Real RTDs, two-point",
        objective=(
            "Validate end-to-end accuracy on real RTDs at two reference points and "
            "confirm 4-wire Kelvin sensing (TESTING_PLAN Part 2)."
        ),
        setup=f"Real 4-wire RTDs, ice bath + reference thermometer. {config.summary()}",
        method="At each reference temperature, read and compute T; compare to the reference.",
        results_intro=f"Budget +/-{args.budget_c:g} degC vs reference thermometer.",
        results_table=markdown_table(
            ["Ch", "T_ref [C]", "R_calc [ohm]", "T_calc [C]", "Err [C]"], rows
        ),
        passed=gate.passed,
        criterion=f"Both points within +/-{args.budget_c:g} degC and Kelvin confirmed.",
        margin="points within budget" if gate.passed else "point(s) out of budget",
        next_action="Proceed to Stage 6 (noise & position independence — headline test).",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())