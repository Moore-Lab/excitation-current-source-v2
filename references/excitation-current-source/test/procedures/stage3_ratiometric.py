#!/usr/bin/env python3
"""Stage 3 — Ratiometric accuracy via substitution (TESTING_PLAN Part 2).

Replace each RTD with a precision resistor / decade box across the RTD range,
read V_ref and V_RTD on the T7, and compute R = R_ref * V_RTD / V_ref. Gate:
recovered R matches the known resistor across the range, within the SPICE budget.
Confirms the ratiometric topology removes the current value from the result.
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from config.board_config import Q_VREF, Q_VRTD  # noqa: E402
from lib.calibration import try_load_calibration  # noqa: E402
from lib.datalog import Recorder  # noqa: E402
from lib.measurement import compute_channel  # noqa: E402
from lib.report import StageReport, markdown_table  # noqa: E402
from lib.rtd import resistance_from_temp, temp_error_from_resistance_error  # noqa: E402
from procedures import common  # noqa: E402

DEFAULT_TEMPS = [-50.0, 0.0, 50.0, 100.0, 150.0]
DEFAULT_TOL = 0.002  # 0.2 % of known R


def _targets(args, config):
    if args.sweep_r:
        return [float(x) for x in args.sweep_r.split(",")]
    if args.known_r is not None:
        return [args.known_r]
    lo, hi = config.temp_range_c
    temps = [t for t in DEFAULT_TEMPS if lo <= t <= hi] or [0.0]
    return [resistance_from_temp(t, config.r0_ohms) for t in temps]


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 3 — ratiometric accuracy (substitution)")
    parser.add_argument("--sweep-r", default=None,
                        help="comma-separated known resistances (ohm) to substitute")
    parser.add_argument("--accuracy-tol", type=float, default=DEFAULT_TOL,
                        help="fractional tolerance of recovered R vs known R")
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 3 — RATIOMETRIC ACCURACY (SUBSTITUTION)", config, args)

    backend, board = common.make_board(args, config)
    board.configure_inputs()
    calib = try_load_calibration(args.out_dir / "calibration.json")
    gate = common.GateLog("Stage 3 — ratiometric accuracy")
    targets = _targets(args, config)

    rows = []
    worst_err = 0.0
    with backend, Recorder("stage3_ratiometric", config, out_dir=args.out_dir,
                           device_info=board.device_info(),
                           conditions="precision resistor / decade box substituted for RTDs") as rec:
        for r_known in targets:
            common.set_mock_rtd(board, r_known)
            common.confirm(f"set decade box / precision R to {r_known:.4f} ohm on all channels", args)
            volts = board.read_voltages(n_avg=args.navg)
            for ch in config.channels:
                i_cal = calib.get(ch) if calib else None
                res = compute_channel(config, ch, volts[ch], i_cal_a=i_cal)
                err = res.r_calc - r_known
                err_frac = err / r_known if r_known else float("nan")
                t_err = temp_error_from_resistance_error(r_known, abs(err), config.r0_ohms)
                rec.log(ch, v_ref=volts[ch].get(Q_VREF, ""), v_rtd=volts[ch][Q_VRTD],
                        r_calc=res.r_calc, t_calc=res.t_calc, r_known=r_known,
                        note=f"substitution {res.method}")
                ok = abs(err_frac) <= args.accuracy_tol
                worst_err = max(worst_err, abs(err_frac))
                gate.record(
                    f"ch{ch} @ {r_known:.2f}ohm within budget", ok,
                    f"R_calc={res.r_calc:.4f} ({err_frac*100:+.3f}%, ~{t_err*1000:.1f} mK)",
                )
                rows.append([ch, f"{r_known:.3f}", f"{res.r_calc:.4f}",
                             f"{err_frac*100:+.3f}", f"{t_err*1000:.2f}"])

    report = StageReport(
        stage_name="Stage 3 — Ratiometric accuracy (substitution)",
        objective=(
            "Prove recovered R = R_ref*V_RTD/V_ref matches known substituted "
            "resistors across the RTD range, within the accuracy budget "
            "(TESTING_PLAN Part 2; the ratiometric correctness criterion)."
        ),
        setup=f"Decade box / precision resistors in place of RTDs. {config.summary()}",
        method=(
            "Substitute each known R across the range; read V_ref and V_RTD "
            f"(navg={args.navg}); compute R and compare to the known value."
        ),
        results_intro=f"Accuracy gate +/-{args.accuracy_tol*100:g}% of known R. "
                      f"Worst-case error this run: {worst_err*100:.3f}%.",
        results_table=markdown_table(
            ["Ch", "R_known [ohm]", "R_calc [ohm]", "Err [%]", "T-equiv err [mK]"], rows
        ),
        passed=gate.passed,
        criterion=f"|R_calc - R_known|/R_known <= {args.accuracy_tol*100:g}% across the range, all channels.",
        margin=f"worst {worst_err*100:.3f}%",
        next_action="Proceed to Stage 4 (compliance headroom at max resistance).",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())