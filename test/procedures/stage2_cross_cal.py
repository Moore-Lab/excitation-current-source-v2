#!/usr/bin/env python3
"""Stage 2 — Cross-calibration (TESTING_PLAN Part 2).

For each channel, substitute a known 0.01 % resistor for the RTD; read V_RTD (T7)
and V_ref (ADS1115) time-aligned; compute and store the per-channel constant

    C = R_known · (V_ref / V_RTD)

This is the critical stage: its output (``cross_cal.json``) is what every later
stage uses to recover ``R = C·V_RTD/V_ref``. Gate: C stable across repeats; the
channel-to-channel spread is as expected (C absorbs R_ref value + gain ratio, so
the CRD current spread does NOT appear in C -- it cancels in the ratio).
"""

import sys
import pathlib

import numpy as np

_T = pathlib.Path(__file__).resolve()
sys.path[:0] = [str(_T.parents[1]), str(_T.parents[2])]  # test/, repo root

from bench import common  # noqa: E402
from bench.datalog import Recorder  # noqa: E402
from bench.report import StageReport, markdown_table  # noqa: E402
from host.calibration import save_cross_cal  # noqa: E402
from host.config import Q_VREF, Q_VRTD  # noqa: E402
from host.measurement import cross_cal_constant  # noqa: E402

DEFAULT_REPEATS = 3
DEFAULT_STABILITY = 5e-4   # C repeatability gate: std/mean across repeats <= 0.05 %


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 2 — cross-calibration")
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS,
                        help="cross-cal measurements per channel (repeatability)")
    parser.add_argument("--stability", type=float, default=DEFAULT_STABILITY,
                        help="max std/mean of C across repeats for the gate")
    parser.add_argument("--instrument", default="(0.01 % reference resistor)",
                        help="known-resistor source, recorded in the cross-cal file")
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 2 — CROSS-CALIBRATION", config, args)

    # R_known: default to R0 (a convenient mid-range value); operator substitutes
    # a 0.01 % part of known value and enters it on the bench.
    r_known = args.known_r if args.known_r is not None else config.r0_ohms
    transport, board = common.make_board(args, config)
    gate = common.GateLog("Stage 2 — cross-calibration")

    c_samples = {ch: [] for ch in config.channels}
    with transport, Recorder("stage2_crosscal", config, out_dir=args.out_dir,
                             device_info=board.device_info(),
                             conditions=f"known R = {r_known:.4f} ohm substituted for each RTD") as rec:
        board.configure()
        common.set_mock_rtd(board, r_known)
        r_known = common.ask_float("known substitution resistance (ohm)", args, auto_value=r_known)
        for _rep in range(max(1, args.repeats)):
            for ch in config.channels:
                v = board.read_channel(ch, t7_navg=args.navg, ads_navg=config.ads_navg)
                c = cross_cal_constant(r_known, v[Q_VRTD], v[Q_VREF])
                c_samples[ch].append(c)
                rec.log(ch, ads_addr=config.ads_map[ch].addr_hex,
                        v_ref=v[Q_VREF], v_rtd=v[Q_VRTD], ratio=v[Q_VRTD] / v[Q_VREF],
                        c_const=c, r_known=r_known, note="cross-cal measurement")

    constants = {ch: float(np.mean(c_samples[ch])) for ch in config.channels}
    rows = []
    for ch in config.channels:
        arr = np.array(c_samples[ch])
        c_mean = float(np.mean(arr))
        c_rel = float(np.std(arr, ddof=1) / c_mean) if arr.size > 1 else 0.0
        ok = c_mean > 0 and np.isfinite(c_mean) and c_rel <= args.stability
        gate.record(f"ch{ch} C stable", ok,
                    f"C={c_mean:.4f} ohm, repeatability {c_rel*1e6:.1f} ppm "
                    f"(<= {args.stability*1e6:g} ppm)")
        rows.append([ch, config.ads_map[ch].addr_hex, f"{c_mean:.4f}", f"{c_rel*1e6:.1f}"])

    # informational: channel-to-channel spread of C (R_ref tol + ADC gain mismatch)
    c_arr = np.array([constants[ch] for ch in config.channels])
    c_spread = float((c_arr.max() - c_arr.min()) / c_arr.mean()) if c_arr.size > 1 else 0.0

    cal_path = save_cross_cal(constants, config, r_known, path=common.calib_path(args),
                              instrument=args.instrument,
                              notes=f"Stage 2; {args.repeats} repeats; R_known={r_known:.4f} ohm")
    print(f"cross-calibration written: {cal_path}")

    report = StageReport(
        stage_name="Stage 2 — Cross-calibration",
        objective=("Capture each channel's cross-cal constant C = R_known·(V_ref/V_RTD), the "
                   "basis for all later resistance recovery (TESTING_PLAN Part 2 Stage 2)."),
        setup=f"0.01 % resistor R_known = {r_known:.4f} ohm in place of each RTD. {config.summary()}",
        method=(f"For each channel, {args.repeats}× read time-aligned V_RTD/V_ref and compute C; "
                "store the mean per channel in cross_cal.json."),
        results_intro=(f"R_known = {r_known:.4f} ohm. Channel-to-channel C spread "
                       f"{c_spread*100:.3f} % (R_ref tol + ADC gain mismatch; CRD current cancels). "
                       f"File: `{cal_path.name}`."),
        results_table=markdown_table(["Ch", "ADS addr", "C [ohm]", "Repeatability [ppm]"], rows),
        passed=gate.passed,
        criterion=f"Each channel's C finite, positive, and repeatable to <= {args.stability*1e6:g} ppm.",
        margin="all C stable" if gate.passed else "C unstable on channel(s)",
        next_action="Proceed to Stage 3 (ratiometric accuracy across the range).",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())
