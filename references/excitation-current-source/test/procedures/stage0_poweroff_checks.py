#!/usr/bin/env python3
"""Stage 0 — Power-off inspection (TESTING_PLAN Part 2).

Visual + DMM continuity checks before any power is applied. Gate: no shorts on
the rail or between force/sense nets, no solder bridges on the REF200. All checks
are operator-confirmed on the bench; auto-confirmed in --mock for a dry run.
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from lib.report import StageReport, markdown_table  # noqa: E402
from procedures import common  # noqa: E402

CHECKS = [
    ("Visual: no obvious solder defects, correct orientation of REF200 / LDO", True),
    ("DMM: rail (+V) to GND is NOT shorted (open or high ohms)", True),
    ("DMM: each channel FORCE+ to SENSE+ continuity sane (Kelvin pair at RTD only)", True),
    ("DMM: FORCE/SENSE nets not shorted to the rail or to each other across channels", True),
    ("DMM: no solder bridges on the REF200 (pins 1/2/7/8 distinct; 6=GND; 3/4/5 open)", True),
    ("Substrate pin 6 continuous to star ground", True),
]


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 0 — power-off inspection")
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 0 — POWER-OFF INSPECTION", config, args)

    gate = common.GateLog("Stage 0 — power-off inspection")
    for prompt, expect in CHECKS:
        ok = common.confirm(prompt, args, auto_value=expect)
        gate.record(prompt, ok)

    report = StageReport(
        stage_name="Stage 0 — Power-off inspection",
        objective=(
            "Confirm the assembled board has no shorts or solder bridges before "
            "power-up. Maps to the Stage-0 go/no-go gate in TESTING_PLAN Part 2."
        ),
        setup=f"DMM in continuity/ohms mode. DUT unpowered. {config.summary()}",
        method="Operator works the checklist; each item is a go/no-go gate.",
        results_table=markdown_table(["Check", "Result", "Detail"], gate.table_rows()),
        passed=gate.passed,
        criterion="No shorts on the rail or between force/sense nets; no REF200 bridges.",
        margin="all checks passed" if gate.passed else "one or more checks failed",
        next_action="Proceed to Stage 1 (power tree) only if all checks pass.",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())