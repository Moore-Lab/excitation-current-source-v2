#!/usr/bin/env python3
"""Stage 4 — Real RTDs, two-point (TESTING_PLAN Part 2).

Mount the real RTDs. Take two reference points -- an ice bath (0 °C -> R0) and a
second known temperature against a reference thermometer -- and confirm the
recovered temperature matches within budget at both. Gate: both points within
the temperature budget on every channel.
"""

import sys
import pathlib

_T = pathlib.Path(__file__).resolve()
sys.path[:0] = [str(_T.parents[1]), str(_T.parents[2])]  # test/, repo root

from bench import common  # noqa: E402
from bench.datalog import Recorder  # noqa: E402
from bench.report import StageReport, markdown_table  # noqa: E402
from host.config import Q_VREF, Q_VRTD  # noqa: E402
from host.measurement import compute_channel  # noqa: E402
from host.rtd import resistance_from_temp  # noqa: E402

DEFAULT_POINTS = [0.0, 100.0]   # ice bath, boiling-water-ish reference
DEFAULT_BUDGET_C = 0.1


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 4 — real RTDs, two-point")
    parser.add_argument("--points", default=None,
                        help="comma-separated reference temperatures (degC)")
    parser.add_argument("--budget-c", type=float, default=DEFAULT_BUDGET_C,
                        help="allowed |T_calc - T_ref| per point")
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 4 — REAL RTDs, TWO-POINT", config, args)

    points = ([float(x) for x in args.points.split(",")] if args.points else DEFAULT_POINTS)
    transport, board = common.make_board(args, config)
    gate = common.GateLog("Stage 4 — real RTDs, two-point")

    rows = []
    worst = 0.0
    with transport:
        board.configure()
        constants = common.load_or_make_cross_cal(board, args, config)
        with Recorder("stage4_real_rtd", config, out_dir=args.out_dir,
                      device_info=board.device_info(),
                      conditions=f"two-point real RTD: {points} degC") as rec:
            for t_ref in points:
                # mock truth: set every RTD to the reference temperature
                common.set_mock_rtd(board, resistance_from_temp(t_ref, config.r0_ohms))
                t_ref = common.ask_float(f"reference thermometer reading (degC) for the ~{t_ref:g} C point",
                                         args, auto_value=t_ref)
                for ch in config.channels:
                    v = board.read_channel(ch, t7_navg=args.navg, ads_navg=config.ads_navg)
                    res = compute_channel(config, ch, v, constants[ch])
                    err = res.t_calc - t_ref
                    worst = max(worst, abs(err))
                    rec.log(ch, ads_addr=config.ads_map[ch].addr_hex,
                            v_ref=v[Q_VREF], v_rtd=v[Q_VRTD], ratio=res.ratio,
                            c_const=res.c_const, r_calc=res.r_calc, t_calc=res.t_calc,
                            note=f"two-point @ {t_ref:g} C")
                    ok = abs(err) <= args.budget_c
                    gate.record(f"ch{ch} @ {t_ref:g}C within budget", ok,
                                f"T_calc={res.t_calc:.3f} C ({err*1e3:+.1f} mK)")
                    rows.append([ch, f"{t_ref:g}", f"{res.t_calc:.3f}", f"{err*1e3:+.1f}"])

    report = StageReport(
        stage_name="Stage 4 — Real RTDs, two-point",
        objective=("Confirm recovered temperature matches a reference at two known points with "
                   "real RTDs mounted (TESTING_PLAN Part 2 Stage 4)."),
        setup=f"Real RTDs; ice bath + second reference temperature. {config.summary()}",
        method=("At each reference point read V_RTD/V_ref, recover T with the Stage-2 C, and "
                "compare to the reference thermometer."),
        results_intro=f"Budget ±{args.budget_c*1e3:g} mK per point. Worst error: {worst*1e3:.1f} mK.",
        results_table=markdown_table(["Ch", "T_ref [C]", "T_calc [C]", "Err [mK]"], rows),
        passed=gate.passed,
        criterion=f"|T_calc - T_ref| <= {args.budget_c*1e3:g} mK at both points, all channels.",
        margin=f"worst {worst*1e3:.1f} mK",
        next_action="Proceed to Stage 5 (noise & position independence — the headline test).",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())