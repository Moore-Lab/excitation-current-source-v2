#!/usr/bin/env python3
"""Stage 1 — Power tree (TESTING_PLAN Part 2).

Bring up the LDO with the REF200 outputs open. Gate: clean +5 V (or +3.3 V)
within tolerance, low ripple. Operator measures the rail with a DMM/scope and
enters the numbers; --mock supplies nominal values for a dry run.
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from lib.report import StageReport, markdown_table  # noqa: E402
from procedures import common  # noqa: E402

NOMINAL_RAIL_V = 5.0
RAIL_TOL = 0.05           # +/-5 %
RIPPLE_LIMIT_MV = 5.0     # mV pk-pk acceptance for a "quiet" rail


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 1 — power tree")
    parser.add_argument("--nominal-rail", type=float, default=NOMINAL_RAIL_V)
    parser.add_argument("--ripple-limit-mv", type=float, default=RIPPLE_LIMIT_MV)
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 1 — POWER TREE", config, args)

    gate = common.GateLog("Stage 1 — power tree")

    common.confirm("REF200 outputs are open / not yet in circuit", args)
    rail_v = common.ask_float("measured rail voltage (V)", args, auto_value=args.nominal_rail)
    ripple_mv = common.ask_float("measured rail ripple (mV pk-pk)", args, auto_value=0.8)

    lo = args.nominal_rail * (1 - RAIL_TOL)
    hi = args.nominal_rail * (1 + RAIL_TOL)
    gate.record(
        "rail within tolerance",
        lo <= rail_v <= hi,
        f"{rail_v:.3f} V in [{lo:.3f}, {hi:.3f}] V",
    )
    gate.record(
        "rail ripple within limit",
        ripple_mv <= args.ripple_limit_mv,
        f"{ripple_mv:.2f} mV pk-pk <= {args.ripple_limit_mv:.2f} mV",
    )

    rows = [
        ["Rail voltage", f"{args.nominal_rail:g} +/-{RAIL_TOL*100:g}%", f"{rail_v:.3f}", "V"],
        ["Rail ripple", f"<= {args.ripple_limit_mv:g}", f"{ripple_mv:.2f}", "mV pp"],
    ]
    report = StageReport(
        stage_name="Stage 1 — Power tree",
        objective=(
            "Verify the LDO produces a clean, in-tolerance rail with the REF200 "
            "out of circuit. Maps to the Stage-1 gate in TESTING_PLAN Part 2."
        ),
        setup=f"DMM + scope on the rail. REF200 outputs open. {config.summary()}",
        method="Power the LDO from the existing supply; measure rail DC and ripple.",
        results_table=markdown_table(["Quantity", "Expected", "Measured", "Unit"], rows),
        passed=gate.passed,
        criterion=f"Rail within +/-{RAIL_TOL*100:g}% and ripple <= {args.ripple_limit_mv:g} mV pk-pk.",
        margin="rail clean" if gate.passed else "rail out of spec",
        next_action="Install/enable the REF200 and proceed to Stage 2 (current verification).",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())