#!/usr/bin/env python3
"""Stage 4 — Compliance headroom (TESTING_PLAN Part 2).

At the largest RTD resistance, confirm the REF200 still regulates: the voltage
across the source = Vrail - (V_ref + V_RTD) must stay above the 2.5 V minimum
(board_spec.md sec.4, target >= 3 V margin). Gate: in compliance at worst case.
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from config.board_config import Q_VREF, Q_VRTD  # noqa: E402
from lib.datalog import Recorder  # noqa: E402
from lib.report import StageReport, markdown_table  # noqa: E402
from lib.rtd import resistance_from_temp  # noqa: E402
from procedures import common  # noqa: E402

COMPLIANCE_MIN_V = 2.5
COMPLIANCE_TARGET_V = 3.0


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 4 — compliance headroom")
    parser.add_argument("--vrail", type=float, default=5.0, help="measured rail voltage (V)")
    parser.add_argument("--min-compliance", type=float, default=COMPLIANCE_MIN_V)
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 4 — COMPLIANCE HEADROOM", config, args)

    backend, board = common.make_board(args, config)
    board.configure_inputs()

    # worst case = highest RTD resistance in the operating band
    r_max = args.known_r if args.known_r is not None else resistance_from_temp(
        config.temp_range_c[1], config.r0_ohms
    )
    common.set_mock_rtd(board, r_max)
    common.confirm(f"set RTD/decade box to worst-case high R = {r_max:.2f} ohm", args)
    vrail = common.ask_float("measured rail voltage (V)", args, auto_value=args.vrail)

    gate = common.GateLog("Stage 4 — compliance headroom")
    rows = []
    with backend, Recorder("stage4_compliance", config, out_dir=args.out_dir,
                           device_info=board.device_info(),
                           conditions=f"worst-case R={r_max:.2f} ohm, Vrail={vrail:.3f} V") as rec:
        volts = board.read_voltages(n_avg=args.navg)
        for ch in config.channels:
            v_ref = volts[ch].get(Q_VREF, config.v_ref_nominal)
            v_rtd = volts[ch][Q_VRTD]
            v_source = vrail - (v_ref + v_rtd)
            rec.log(ch, v_ref=v_ref, v_rtd=v_rtd, r_known=r_max,
                    note=f"compliance V_source={v_source:.4f}")
            ok = v_source >= args.min_compliance
            flag = "" if v_source >= COMPLIANCE_TARGET_V else " (below target 3 V)"
            gate.record(f"ch{ch} in compliance", ok, f"V_source={v_source:.3f} V{flag}")
            rows.append([ch, f"{vrail:.3f}", f"{(v_ref+v_rtd)*1e3:.2f}", f"{v_source:.3f}",
                         "PASS" if ok else "FAIL"])

    report = StageReport(
        stage_name="Stage 4 — Compliance headroom",
        objective=(
            "Confirm each REF200 source keeps >= 2.5 V across it at the highest "
            "RTD resistance and the measured rail (TESTING_PLAN Part 2; "
            "board_spec.md sec.4 compliance check)."
        ),
        setup=f"Worst-case high R substituted; rail measured. {config.summary()}",
        method="Set max R, read V_ref+V_RTD, compute V_source = Vrail - (V_ref+V_RTD).",
        results_intro=f"Worst-case R = {r_max:.2f} ohm, Vrail = {vrail:.3f} V, "
                      f"min compliance {args.min_compliance:g} V (target {COMPLIANCE_TARGET_V:g} V).",
        results_table=markdown_table(
            ["Ch", "Vrail [V]", "V_ref+V_RTD [mV]", "V_source [V]", "Gate"], rows
        ),
        passed=gate.passed,
        criterion=f"V_source >= {args.min_compliance:g} V on every channel at worst case.",
        margin="in compliance" if gate.passed else "compliance lost",
        next_action="Proceed to Stage 5 (real RTDs, two-point).",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())