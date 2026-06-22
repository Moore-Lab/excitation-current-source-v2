#!/usr/bin/env python3
"""Stage 6 — Crosstalk (TESTING_PLAN Part 2).

Perturb one channel (warm one RTD) and confirm the others do not move beyond the
noise floor. Shared star-ground return impedance is the coupling path; this
bounds it. Gate: no victim channel shifts more than the crosstalk budget when the
aggressor is perturbed.
"""

import sys
import pathlib

import numpy as np

_T = pathlib.Path(__file__).resolve()
sys.path[:0] = [str(_T.parents[1]), str(_T.parents[2])]  # test/, repo root

from bench import common  # noqa: E402
from bench.datalog import Recorder  # noqa: E402
from bench.report import StageReport, markdown_table  # noqa: E402
from host.config import Q_VREF, Q_VRTD  # noqa: E402
from host.measurement import compute_channel  # noqa: E402
from host.rtd import resistance_from_temp  # noqa: E402

DEFAULT_BUDGET_MK = 20.0       # max allowed victim shift (milli-degC)
DEFAULT_AGGRESSOR_DT = 20.0    # how much to warm the aggressor channel (degC)
DEFAULT_AVG_READS = 32         # full reads averaged per before/after point (quasi-DC)


def _read_temps(board, config, constants, args):
    """Averaged per-channel recovery -- crosstalk is a DC shift, so we settle the
    read well below the budget before differencing the before/after points."""
    acc = {ch: {Q_VRTD: [], Q_VREF: []} for ch in config.channels}
    for _ in range(max(1, args.avg_reads)):
        volts = board.read_channels(t7_navg=args.navg, ads_navg=config.ads_navg)
        for ch in config.channels:
            acc[ch][Q_VRTD].append(volts[ch][Q_VRTD])
            acc[ch][Q_VREF].append(volts[ch][Q_VREF])
    out = {}
    for ch in config.channels:
        v = {Q_VRTD: float(np.mean(acc[ch][Q_VRTD])), Q_VREF: float(np.mean(acc[ch][Q_VREF]))}
        out[ch] = compute_channel(config, ch, v, constants[ch])
    return out


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 6 — crosstalk")
    parser.add_argument("--budget-mk", type=float, default=DEFAULT_BUDGET_MK,
                        help="max allowed victim shift, milli-degC")
    parser.add_argument("--aggressor", type=int, default=0, help="channel to perturb")
    parser.add_argument("--aggressor-dt", type=float, default=DEFAULT_AGGRESSOR_DT,
                        help="temperature step applied to the aggressor (degC)")
    parser.add_argument("--base-temp", type=float, default=0.0,
                        help="baseline temperature for all channels (mock)")
    parser.add_argument("--avg-reads", type=int, default=DEFAULT_AVG_READS,
                        help="full reads averaged per before/after point (quasi-DC)")
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 6 — CROSSTALK", config, args)

    aggressor = args.aggressor if args.aggressor in config.channels else config.channels[0]
    transport, board = common.make_board(args, config)
    gate = common.GateLog("Stage 6 — crosstalk")

    rows = []
    with transport:
        board.configure()
        constants = common.load_or_make_cross_cal(board, args, config)
        common.set_mock_rtd(board, resistance_from_temp(args.base_temp, config.r0_ohms))
        common.confirm(f"all channels stable at ~{args.base_temp:g} C", args)

        with Recorder("stage6_crosstalk", config, out_dir=args.out_dir,
                      device_info=board.device_info(),
                      conditions=f"aggressor ch{aggressor} +{args.aggressor_dt:g} C") as rec:
            before = _read_temps(board, config, constants, args)
            for ch in config.channels:
                rec.log(ch, c_const=constants[ch], r_calc=before[ch].r_calc,
                        t_calc=before[ch].t_calc, note="baseline (aggressor cold)")

            # perturb only the aggressor channel
            common.set_mock_rtd(board, resistance_from_temp(args.base_temp + args.aggressor_dt,
                                                            config.r0_ohms), channels=[aggressor])
            common.confirm(f"warm ONLY channel {aggressor} by ~{args.aggressor_dt:g} C", args)
            after = _read_temps(board, config, constants, args)
            for ch in config.channels:
                rec.log(ch, c_const=constants[ch], r_calc=after[ch].r_calc,
                        t_calc=after[ch].t_calc, note="aggressor warm")

        budget_c = args.budget_mk * 1e-3
        for ch in config.channels:
            shift = after[ch].t_calc - before[ch].t_calc
            if ch == aggressor:
                gate.record(f"aggressor ch{ch} responded", abs(shift) > 0.5 * args.aggressor_dt,
                            f"{shift:+.3f} C (expected ~{args.aggressor_dt:g} C)")
            else:
                gate.record(f"victim ch{ch} quiet", abs(shift) <= budget_c,
                            f"{shift*1e3:+.2f} mK <= {args.budget_mk:g} mK")
            rows.append([ch, "aggressor" if ch == aggressor else "victim",
                         f"{before[ch].t_calc:.3f}", f"{after[ch].t_calc:.3f}", f"{shift*1e3:+.2f}"])

    report = StageReport(
        stage_name="Stage 6 — Crosstalk",
        objective=("Confirm perturbing one channel does not move the others beyond the budget "
                   "(TESTING_PLAN Part 2 Stage 6)."),
        setup=f"All channels at ~{args.base_temp:g} C; aggressor = ch{aggressor}. {config.summary()}",
        method=(f"Read all channels cold; warm only ch{aggressor} by ~{args.aggressor_dt:g} C; re-read; "
                "compare each victim's shift to the budget."),
        results_intro=f"Crosstalk budget ±{args.budget_mk:g} mK on victim channels.",
        results_table=markdown_table(
            ["Ch", "Role", "T before [C]", "T after [C]", "Shift [mK]"], rows),
        passed=gate.passed,
        criterion=f"Every victim shift <= {args.budget_mk:g} mK while the aggressor responds fully.",
        margin="no measurable coupling" if gate.passed else "victim coupling detected",
        next_action="Proceed to Stage 7 (thermal soak / C drift).",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())