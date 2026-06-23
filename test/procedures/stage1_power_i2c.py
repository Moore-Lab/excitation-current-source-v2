#!/usr/bin/env python3
"""Stage 1 — Power & I²C bring-up (TESTING_PLAN Part 2).

Bring up the rail; confirm it is clean and in tolerance. Then scan the I²C bus
and confirm every expected ADS1115 (0x48–0x4B per the channel count) is present,
and read each channel's V_ref raw to confirm it is sane and stable. Gate: rail OK
AND all expected ADS1115 addresses present AND every V_ref inside the PGA range.
"""

import sys
import pathlib

_T = pathlib.Path(__file__).resolve()
sys.path[:0] = [str(_T.parents[1]), str(_T.parents[2])]  # test/, repo root

from bench import common  # noqa: E402
from bench.datalog import Recorder  # noqa: E402
from bench.report import StageReport, markdown_table  # noqa: E402
from host.config import Q_VREF, Q_VRTD  # noqa: E402

NOMINAL_RAIL_V = 5.0
RAIL_TOL = 0.05           # ±5 %
RIPPLE_LIMIT_MV = 5.0     # mV pk-pk for a "quiet" rail


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 1 — power & I²C bring-up")
    parser.add_argument("--nominal-rail", type=float, default=NOMINAL_RAIL_V)
    parser.add_argument("--ripple-limit-mv", type=float, default=RIPPLE_LIMIT_MV)
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 1 — POWER & I²C BRING-UP", config, args)

    gate = common.GateLog("Stage 1 — power & I²C bring-up")

    # --- rail ---
    rail_v = common.ask_float("measured rail voltage (V)", args, auto_value=args.nominal_rail)
    ripple_mv = common.ask_float("measured rail ripple (mV pk-pk)", args, auto_value=0.8)
    lo, hi = args.nominal_rail * (1 - RAIL_TOL), args.nominal_rail * (1 + RAIL_TOL)
    gate.record("rail within tolerance", lo <= rail_v <= hi,
                f"{rail_v:.3f} V in [{lo:.3f}, {hi:.3f}] V")
    gate.record("rail ripple within limit", ripple_mv <= args.ripple_limit_mv,
                f"{ripple_mv:.2f} mV pk-pk <= {args.ripple_limit_mv:.2f} mV")

    # --- I²C scan + raw V_ref ---
    transport, board = common.make_board(args, config)
    expected = config.ads_addresses
    rows = []
    with transport:
        board.configure()
        found = board.scan_i2c()
        present_expected = [a for a in expected if a in found]
        gate.record("all expected ADS1115 present",
                    set(expected).issubset(set(found)),
                    f"expected {[hex(a) for a in expected]}, found {[hex(a) for a in found]}")

        with Recorder("stage1_bringup", config, out_dir=args.out_dir,
                      device_info=board.device_info(),
                      conditions=f"rail {rail_v:.3f} V; I²C scan + raw V_ref") as rec:
            for ch in config.channels:
                v = board.read_channel(ch, t7_navg=args.navg, ads_navg=config.ads_navg)
                vref, vrtd = v[Q_VREF], v[Q_VRTD]
                inp = config.ads_map[ch]
                rec.log(ch, ads_addr=inp.addr_hex, v_ref=vref, v_rtd=vrtd,
                        note="bring-up raw read")
                in_range = abs(vref) < config.ads_range_v and vref > 0
                gate.record(f"ch{ch} V_ref sane ({inp.addr_hex} {inp.pair_label})", in_range,
                            f"V_ref={vref*1e3:.2f} mV (<{config.ads_range_v*1e3:g} mV FS), "
                            f"V_RTD={vrtd*1e3:.3f} mV")
                rows.append([ch, inp.addr_hex, inp.pair_label, f"{vref*1e3:.2f}", f"{vrtd*1e3:.3f}"])

    report = StageReport(
        stage_name="Stage 1 — Power & I²C bring-up",
        objective=("Verify a clean rail, detect every ADS1115 on the I²C bus, and confirm "
                   "each V_ref reads sane (TESTING_PLAN Part 2 Stage 1)."),
        setup=f"DMM/scope on the rail; LJM I²C on the T7 digital lines. {config.summary()}",
        method=("Measure rail DC + ripple; scan I²C addresses 0x48–0x4B; read each channel's "
                f"V_ref (ADS, navg={config.ads_navg}) and V_RTD (T7, navg={args.navg})."),
        results_intro=f"Expected ADS1115: {[hex(a) for a in expected]}; "
                      f"present: {[hex(a) for a in present_expected]}.",
        results_table=markdown_table(
            ["Ch", "ADS addr", "Input", "V_ref [mV]", "V_RTD [mV]"], rows),
        passed=gate.passed,
        criterion=("Rail within ±5 % and quiet; all expected ADS1115 present; every V_ref "
                   "positive and within the PGA full-scale."),
        margin="rail + bus + V_ref all sane" if gate.passed else "see failed gate(s)",
        next_action="Proceed to Stage 2 (cross-calibration).",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())
