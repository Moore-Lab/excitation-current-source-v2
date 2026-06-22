#!/usr/bin/env python3
"""Stage 7 — Thermal soak / C drift (TESTING_PLAN Part 2).

Soak at a fixed temperature with a known resistor in place of each RTD and watch
the cross-cal constant **C drift** over time. C drift directly measures the
accuracy term this architecture is limited by: R_ref tempco + the *relative* gain
tempco of the two ADCs (board_spec.md "The measurement"). Gate: |C drift| within
budget on every channel; if it drifts more than predicted, improve the thermal
coupling of the two converters or shorten the recal interval.
"""

import sys
import time
import pathlib

import numpy as np

_T = pathlib.Path(__file__).resolve()
sys.path[:0] = [str(_T.parents[1]), str(_T.parents[2])]  # test/, repo root

from bench import common  # noqa: E402
from bench.datalog import Recorder  # noqa: E402
from bench.report import StageReport, markdown_table  # noqa: E402
from bench.stats import noise_stats  # noqa: E402
from host.config import Q_VREF, Q_VRTD  # noqa: E402
from host.measurement import cross_cal_constant  # noqa: E402

DEFAULT_DRIFT_BUDGET_PPM = 100.0   # allowed end-to-end C drift over the soak (ppm)


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 7 — thermal soak / C drift")
    parser.add_argument("--drift-budget-ppm", type=float, default=DEFAULT_DRIFT_BUDGET_PPM)
    parser.add_argument("--soak-temp", type=float, default=25.0)
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 7 — THERMAL SOAK / C DRIFT", config, args)

    # Known resistor stands in for each RTD so we can recompute C over the soak.
    r_known = args.known_r if args.known_r is not None else config.r0_ohms
    transport, board = common.make_board(args, config)
    gate = common.GateLog("Stage 7 — thermal soak / C drift")

    c_series = {ch: [] for ch in config.channels}
    with transport, Recorder("stage7_soak", config, out_dir=args.out_dir,
                             device_info=board.device_info(),
                             conditions=f"soak at {args.soak_temp:g} C; known R = {r_known:.4f} ohm; "
                                        f"{args.samples} samples @ {args.interval_s:g}s") as rec:
        board.configure()
        common.set_mock_rtd(board, r_known)
        r_known = common.ask_float("known substitution resistance (ohm) held through the soak",
                                   args, auto_value=r_known)
        common.confirm(f"hold the board at a fixed {args.soak_temp:g} C for the soak", args)
        for i in range(args.samples):
            for ch in config.channels:
                v = board.read_channel(ch, t7_navg=args.navg, ads_navg=config.ads_navg)
                c = cross_cal_constant(r_known, v[Q_VRTD], v[Q_VREF])
                c_series[ch].append(c)
                rec.log(ch, ads_addr=config.ads_map[ch].addr_hex,
                        v_ref=v[Q_VREF], v_rtd=v[Q_VRTD], ratio=v[Q_VRTD] / v[Q_VREF],
                        c_const=c, r_known=r_known, note="soak C sample")
            if args.interval_s > 0 and i < args.samples - 1:
                time.sleep(args.interval_s)

    rows = []
    for ch in config.channels:
        arr = np.array(c_series[ch])
        st = noise_stats(arr)
        c0 = st.mean if st.mean else 1.0
        drift_ppm = (st.drift / c0) * 1e6
        noise_ppm = (st.std / c0) * 1e6
        ok = abs(drift_ppm) <= args.drift_budget_ppm
        gate.record(f"ch{ch} C drift within budget", ok,
                    f"drift {drift_ppm:+.1f} ppm <= {args.drift_budget_ppm:g} ppm")
        rows.append([ch, f"{st.mean:.4f}", f"{drift_ppm:+.1f}", f"{noise_ppm:.1f}"])

    report = StageReport(
        stage_name="Stage 7 — Thermal soak / C drift",
        objective=("Confirm the cross-cal constant C is stable over a soak; its drift is the "
                   "R_ref + relative-ADC-gain-tempco term that limits accuracy between recals "
                   "(TESTING_PLAN Part 2 Stage 7)."),
        setup=f"Fixed {args.soak_temp:g} C soak; known R = {r_known:.4f} ohm per channel. "
              f"{config.summary()}. {args.samples} samples @ {args.interval_s:g}s.",
        method="Recompute C = R_known·(V_ref/V_RTD) over the soak; fit end-to-end drift; gate in ppm.",
        results_intro=f"Drift budget ±{args.drift_budget_ppm:g} ppm of C over the record.",
        results_table=markdown_table(
            ["Ch", "C mean [ohm]", "C drift [ppm]", "C noise [ppm]"], rows),
        passed=gate.passed,
        criterion=(f"|C drift| <= {args.drift_budget_ppm:g} ppm per channel; consistent with the "
                   "R_ref + relative-gain tempco prediction."),
        margin="C stable over soak" if gate.passed else "C drift exceeds budget",
        next_action="Proceed to Stage 8 (CRD noise check).",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())
