#!/usr/bin/env python3
"""Stage 0 — Power-off inspection (TESTING_PLAN Part 2).

Continuity checks with the board unpowered: no shorts on the rail, no bridges
between any RTD force/sense lines, and -- new for this board -- no short on the
I²C bus (SDA/SCL to each other, to the rail, or to ground). Operator confirms
each; ``--mock`` auto-confirms for a dry run. Gate: no shorts/bridges.
"""

import sys
import pathlib

_T = pathlib.Path(__file__).resolve()
sys.path[:0] = [str(_T.parents[1]), str(_T.parents[2])]  # test/, repo root

from bench import common  # noqa: E402
from bench.report import StageReport, markdown_table  # noqa: E402


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 0 — power-off inspection")
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 0 — POWER-OFF INSPECTION", config, args)

    gate = common.GateLog("Stage 0 — power-off inspection")
    checks = [
        ("rail not shorted to GND", "ohmmeter across rail->GND reads open (not ~0 Ω)"),
        ("no force/sense bridges", "no continuity between Force±/Sense± within or across channels"),
        ("I²C bus not shorted", "SDA-SCL, SDA-rail, SCL-GND etc. all read open"),
        ("R_ref pads isolated", "no short across any R_ref / ADS1115 differential pair"),
    ]
    rows = []
    for name, prompt in checks:
        ok = common.confirm(prompt, args)
        gate.record(name, ok, prompt)
        rows.append([name, "open / no bridge", "PASS" if ok else "FAIL"])

    report = StageReport(
        stage_name="Stage 0 — Power-off inspection",
        objective="Confirm no shorts/bridges before applying power (TESTING_PLAN Part 2 Stage 0).",
        setup=f"Board unpowered, DMM in continuity/resistance mode. {config.summary()}",
        method="Probe each net pair listed; every check must read open.",
        results_table=markdown_table(["Check", "Expected", "Result"], rows),
        passed=gate.passed,
        criterion="No shorts on the rail, force/sense lines, or the I²C bus.",
        margin="all checks open" if gate.passed else "short/bridge found",
        next_action="Apply power and proceed to Stage 1 (power & I²C bring-up).",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())
