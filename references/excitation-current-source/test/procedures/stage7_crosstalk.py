#!/usr/bin/env python3
"""Stage 7 — Crosstalk (TESTING_PLAN Part 2).

Perturb one channel (e.g. warm one RTD) and confirm the others don't move beyond
noise. Gate: no measurable cross-coupling into the unperturbed channels. Probes
the shared star-ground return impedance path (board_spec.md sec.6).
"""

import sys
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from lib.calibration import try_load_calibration  # noqa: E402
from lib.datalog import Recorder  # noqa: E402
from lib.measurement import compute_channel  # noqa: E402
from lib.report import StageReport, markdown_table  # noqa: E402
from lib.rtd import resistance_from_temp  # noqa: E402
from lib.stats import noise_stats  # noqa: E402
from procedures import common  # noqa: E402

DEFAULT_PERTURB_C = 5.0     # how much the aggressor channel is warmed
DEFAULT_BUDGET_C = 0.05     # max allowed shift on a victim channel


def _read_temps(board, config, calib, n_avg):
    volts = board.read_voltages(n_avg=n_avg)
    out = {}
    for ch in config.channels:
        i_cal = calib.get(ch) if calib else None
        out[ch] = compute_channel(config, ch, volts[ch], i_cal_a=i_cal).t_calc
    return out


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 7 — crosstalk")
    parser.add_argument("--aggressor", type=int, default=0, help="channel to perturb")
    parser.add_argument("--perturb-c", type=float, default=DEFAULT_PERTURB_C)
    parser.add_argument("--budget-c", type=float, default=DEFAULT_BUDGET_C)
    parser.add_argument("--base-temp", type=float, default=25.0)
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 7 — CROSSTALK", config, args)

    backend, board = common.make_board(args, config)
    board.configure_inputs()
    calib = try_load_calibration(args.out_dir / "calibration.json")
    agg = args.aggressor

    gate = common.GateLog("Stage 7 — crosstalk")
    rows = []
    with backend, Recorder("stage7_crosstalk", config, out_dir=args.out_dir,
                           device_info=board.device_info(),
                           conditions=f"aggressor ch{agg} +{args.perturb_c:g}C") as rec:
        # start all channels at the base temperature
        common.set_mock_rtd(board, resistance_from_temp(args.base_temp, config.r0_ohms))
        common.confirm(f"hold all channels stable at ~{args.base_temp:g} C", args)

        # noise reference (so the gate is the larger of budget and measured noise)
        noise_samp = {ch: [] for ch in config.channels}
        for _ in range(max(8, args.samples // 4)):
            t = _read_temps(board, config, calib, args.navg)
            for ch in config.channels:
                noise_samp[ch].append(t[ch])
        baseline = {ch: noise_stats(np.array(noise_samp[ch])).mean for ch in config.channels}
        noise = {ch: noise_stats(np.array(noise_samp[ch])).std for ch in config.channels}

        # perturb only the aggressor channel
        common.set_mock_rtd(board, resistance_from_temp(args.base_temp + args.perturb_c, config.r0_ohms),
                            channels=[agg])
        common.confirm(f"warm aggressor channel {agg} by ~{args.perturb_c:g} C", args)

        perturbed = _read_temps(board, config, calib, args.navg)
        for ch in config.channels:
            shift = perturbed[ch] - baseline[ch]
            rec.log(ch, v_rtd="", t_calc=perturbed[ch],
                    note=f"shift={shift:+.4f}C aggressor={agg}")
            if ch == agg:
                gate.record(f"ch{ch} (aggressor) responded", abs(shift) > args.budget_c,
                            f"shift {shift:+.3f} C (expected ~{args.perturb_c:g} C)")
                rows.append([ch, "aggressor", f"{shift:+.4f}", "n/a"])
            else:
                thr = max(args.budget_c, 5.0 * noise[ch])
                ok = abs(shift) <= thr
                gate.record(f"ch{ch} (victim) quiet", ok,
                            f"shift {shift*1e3:+.2f} mK <= {thr*1e3:.1f} mK")
                rows.append([ch, "victim", f"{shift*1e3:+.3f} mK", "PASS" if ok else "FAIL"])

    report = StageReport(
        stage_name="Stage 7 — Crosstalk",
        objective=(
            "Confirm perturbing one channel does not couple into the others beyond "
            "noise (TESTING_PLAN Part 2; star-ground return-impedance path)."
        ),
        setup=f"All channels stable; aggressor ch{agg} warmed. {config.summary()}",
        method="Record victim channels before/after warming the aggressor; gate the shift.",
        results_intro=f"Aggressor ch{agg} perturbed by ~{args.perturb_c:g} C; "
                      f"victim budget +/-{args.budget_c*1e3:g} mK (or 5x measured noise).",
        results_table=markdown_table(["Ch", "Role", "Shift", "Gate"], rows),
        passed=gate.passed,
        criterion="No victim channel shifts beyond budget when the aggressor is perturbed.",
        margin="no measurable coupling" if gate.passed else "cross-coupling detected",
        next_action="Proceed to Stage 8 (thermal soak / drift).",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())