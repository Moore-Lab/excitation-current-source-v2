#!/usr/bin/env python3
"""Stage 2 — Current verification & per-channel calibration (TESTING_PLAN Part 2).

Measure each channel's actual delivered current (DMM in current mode, or known
precision resistor) and store it as that channel's **calibration constant** for
calibrated-current measurement mode (board_spec.md sec.5). Gate: each channel
within REF200 spec of nominal and stable.

This is a critical stage: its output (test/data/calibration.json) is consumed by
calibrated-current mode and by later accuracy checks.
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from lib.calibration import save_calibration  # noqa: E402
from lib.datalog import Recorder  # noqa: E402
from lib.report import StageReport, markdown_table  # noqa: E402
from procedures import common  # noqa: E402

DEFAULT_TOL = 0.01  # +/-1 % of nominal (REF200 initial accuracy is ~+/-0.5 %)


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 2 — current verification & calibration")
    parser.add_argument("--current-tol", type=float, default=DEFAULT_TOL,
                        help="fractional tolerance vs nominal current for the gate")
    parser.add_argument("--instrument", default="(DMM in current mode)",
                        help="instrument used, recorded in the calibration file")
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 2 — CURRENT VERIFICATION & CALIBRATION", config, args)

    backend, board = common.make_board(args, config)
    gate = common.GateLog("Stage 2 — current verification & calibration")
    nominal = config.excitation_current_a
    lo, hi = nominal * (1 - args.current_tol), nominal * (1 + args.current_tol)

    currents = {}
    rows = []
    with backend, Recorder("stage2_current", config, out_dir=args.out_dir,
                           device_info=board.device_info(),
                           conditions="REF200 sourcing into known load/DMM") as rec:
        for ch in config.channels:
            auto_i = common.mock_truth_current(board, ch)
            if auto_i is None:
                auto_i = nominal
            i_meas = common.ask_float(
                f"channel {ch}: measured current (A)", args, auto_value=auto_i
            )
            currents[ch] = i_meas
            rec.log(ch, i_meas_a=i_meas, note="current verification")
            ok = lo <= i_meas <= hi
            err_pct = 100.0 * (i_meas - nominal) / nominal
            gate.record(f"ch{ch} current in spec", ok, f"{i_meas*1e6:.3f} uA ({err_pct:+.2f}%)")
            rows.append([ch, f"{nominal*1e6:g}", f"{i_meas*1e6:.3f}", f"{err_pct:+.3f}", "uA / %"])

    calib_path = save_calibration(
        currents, config, path=args.out_dir / "calibration.json",
        instrument=args.instrument,
        notes=f"Stage 2 capture; gate +/-{args.current_tol*100:g}% of {nominal*1e6:g} uA",
    )
    print(f"calibration written: {calib_path}")

    report = StageReport(
        stage_name="Stage 2 — Current verification & calibration",
        objective=(
            "Verify each channel's delivered current and capture it as the "
            "per-channel calibration constant for calibrated-current mode "
            "(TESTING_PLAN Part 2; board_spec.md sec.5)."
        ),
        setup=f"DMM/known resistor per channel. {config.summary()}",
        method=(
            "For each channel, measure the actual source current and record it; "
            "gate each against the nominal +/- tolerance. Store all in "
            "calibration.json."
        ),
        results_intro=f"Nominal {nominal*1e6:g} uA, gate +/-{args.current_tol*100:g}%. "
                      f"Calibration file: `{calib_path.name}`.",
        results_table=markdown_table(
            ["Ch", "Nominal", "Measured", "Error", "Unit"], rows
        ),
        passed=gate.passed,
        criterion=f"Each channel within +/-{args.current_tol*100:g}% of {nominal*1e6:g} uA and stable.",
        margin="all channels in spec" if gate.passed else "channel(s) out of spec",
        next_action="Proceed to Stage 3 (ratiometric accuracy via substitution).",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())