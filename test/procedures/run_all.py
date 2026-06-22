#!/usr/bin/env python3
"""Run the full bring-up sequence (Stage 0 -> Stage 8) in order.

Convenience driver for a dry run or a full bench pass. Stops at the first failed
stage (each stage is a go/no-go gate) unless --keep-going. Common flags pass
through to every stage.

    python procedures/run_all.py --mock --yes
    python procedures/run_all.py --real --rtd Pt1000 --channels 3
"""

import sys
import pathlib

_T = pathlib.Path(__file__).resolve()
sys.path[:0] = [str(_T.parents[1]), str(_T.parents[2])]  # test/, repo root

from procedures import (  # noqa: E402
    stage0_poweroff_checks,
    stage1_power_i2c,
    stage2_cross_cal,
    stage3_ratiometric,
    stage4_real_rtd,
    stage5_noise_position,
    stage6_crosstalk,
    stage7_thermal_soak,
    stage8_crd_noise,
)

STAGES = [
    ("Stage 0", stage0_poweroff_checks),
    ("Stage 1", stage1_power_i2c),
    ("Stage 2", stage2_cross_cal),
    ("Stage 3", stage3_ratiometric),
    ("Stage 4", stage4_real_rtd),
    ("Stage 5", stage5_noise_position),
    ("Stage 6", stage6_crosstalk),
    ("Stage 7", stage7_thermal_soak),
    ("Stage 8", stage8_crd_noise),
]


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    keep_going = "--keep-going" in argv
    argv = [a for a in argv if a != "--keep-going"]

    results = []
    overall = 0
    for name, module in STAGES:
        print("\n" + "#" * 72)
        print(f"# {name}")
        print("#" * 72)
        rc = module.main(argv)
        results.append((name, rc))
        if rc != 0:
            overall = 1
            if not keep_going:
                print(f"\n{name} FAILED (rc={rc}); stopping (use --keep-going to continue).")
                break

    print("\n" + "=" * 72)
    print("SEQUENCE SUMMARY")
    for name, rc in results:
        print(f"  {name}: {'PASS' if rc == 0 else 'FAIL'}")
    print("=" * 72)
    return overall


if __name__ == "__main__":
    raise SystemExit(main())