#!/usr/bin/env python3
"""Stage 3 — Ratiometric accuracy (TESTING_PLAN Part 2).

Sweep known resistors / a decade box across the RTD range; recover
``R = C·V_RTD/V_ref`` using the Stage-2 constants. Gate: recovered R matches the
known value across the range within the SPICE-predicted budget, on every channel.
Confirms the dual-ADC ratiometric topology removes the CRD current from the
result and that C transfers correctly across the range. Verify Kelvin separately
(vary lead length -> no shift).
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
from host.rtd import resistance_from_temp, temp_error_from_resistance_error  # noqa: E402

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
    parser = common.build_arg_parser("Stage 3 — ratiometric accuracy")
    parser.add_argument("--sweep-r", default=None,
                        help="comma-separated known resistances (ohm) to substitute")
    parser.add_argument("--accuracy-tol", type=float, default=DEFAULT_TOL,
                        help="fractional tolerance of recovered R vs known R")
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 3 — RATIOMETRIC ACCURACY", config, args)

    transport, board = common.make_board(args, config)
    gate = common.GateLog("Stage 3 — ratiometric accuracy")
    targets = _targets(args, config)

    rows = []
    worst_err = 0.0
    with transport:
        board.configure()
        constants = common.load_or_make_cross_cal(board, args, config)
        with Recorder("stage3_ratiometric", config, out_dir=args.out_dir,
                      device_info=board.device_info(),
                      conditions="precision resistor / decade box substituted for RTDs") as rec:
            for r_known in targets:
                common.set_mock_rtd(board, r_known)
                common.confirm(f"set decade box / precision R to {r_known:.4f} ohm on all channels", args)
                for ch in config.channels:
                    v = board.read_channel(ch, t7_navg=args.navg, ads_navg=config.ads_navg)
                    res = compute_channel(config, ch, v, constants[ch])
                    err_frac = (res.r_calc - r_known) / r_known if r_known else float("nan")
                    t_err = temp_error_from_resistance_error(r_known, abs(res.r_calc - r_known), config.r0_ohms)
                    rec.log(ch, ads_addr=config.ads_map[ch].addr_hex,
                            v_ref=v[Q_VREF], v_rtd=v[Q_VRTD], ratio=res.ratio,
                            c_const=res.c_const, r_calc=res.r_calc, t_calc=res.t_calc,
                            r_known=r_known, note="ratiometric substitution")
                    ok = abs(err_frac) <= args.accuracy_tol
                    worst_err = max(worst_err, abs(err_frac))
                    gate.record(f"ch{ch} @ {r_known:.2f}ohm within budget", ok,
                                f"R_calc={res.r_calc:.4f} ({err_frac*100:+.3f}%, ~{t_err*1e3:.1f} mK)")
                    rows.append([ch, f"{r_known:.3f}", f"{res.r_calc:.4f}",
                                 f"{err_frac*100:+.3f}", f"{t_err*1e3:.2f}"])

    report = StageReport(
        stage_name="Stage 3 — Ratiometric accuracy",
        objective=("Prove recovered R = C·V_RTD/V_ref matches known substituted resistors across "
                   "the RTD range within budget (TESTING_PLAN Part 2 Stage 3)."),
        setup=f"Decade box / precision resistors in place of RTDs. {config.summary()}",
        method=(f"Substitute each known R across the range; read V_RTD (T7) + V_ref (ADS, "
                f"navg={config.ads_navg}); compute R with the Stage-2 C and compare."),
        results_intro=f"Accuracy gate ±{args.accuracy_tol*100:g}% of known R. "
                      f"Worst-case error this run: {worst_err*100:.3f}%.",
        results_table=markdown_table(
            ["Ch", "R_known [ohm]", "R_calc [ohm]", "Err [%]", "T-equiv err [mK]"], rows),
        passed=gate.passed,
        criterion=f"|R_calc - R_known|/R_known <= {args.accuracy_tol*100:g}% across the range, all channels.",
        margin=f"worst {worst_err*100:.3f}%",
        next_action="Proceed to Stage 4 (real RTDs, two-point).",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())