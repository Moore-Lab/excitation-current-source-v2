#!/usr/bin/env python3
"""Stage 8 — CRD noise check (TESTING_PLAN Part 2, the source risk).

The one weakness this architecture tolerates only if it is small: current-
regulator-diode (CRD) current noise. It cancels in the ratiometric result (same I
through R_ref and the RTD), but bound it directly on hardware by measuring the
*fractional* noise of V_ref = I·R_ref over a scan -- where it does NOT cancel.
Gate: per-channel fractional V_ref noise below the floor. If it fails, the CRD
must be swapped for a reference+op-amp source; the ratiometric readout is unchanged.
"""

import sys
import pathlib

import numpy as np

_T = pathlib.Path(__file__).resolve()
sys.path[:0] = [str(_T.parents[1]), str(_T.parents[2])]  # test/, repo root

from bench import common  # noqa: E402
from bench.datalog import Recorder  # noqa: E402
from bench.report import StageReport, markdown_table  # noqa: E402
from bench.stats import noise_stats  # noqa: E402

DEFAULT_FLOOR_PPM = 200.0   # max fractional V_ref noise, rms (CRD + ADS single-shot)


def main(argv=None) -> int:
    parser = common.build_arg_parser("Stage 8 — CRD noise check")
    parser.add_argument("--floor-ppm", type=float, default=DEFAULT_FLOOR_PPM,
                        help="max fractional V_ref noise (ppm rms)")
    parser.add_argument("--crd-noise-ppm", type=float, default=None,
                        help="mock: inject this fractional CRD current noise (ppm)")
    args = parser.parse_args(argv)
    config = common.config_from_args(args)
    common.header("STAGE 8 — CRD NOISE CHECK", config, args)

    transport, board = common.make_board(args, config)
    gate = common.GateLog("Stage 8 — CRD noise check")

    if args.crd_noise_ppm is not None:
        common.set_mock_crd_noise(board, args.crd_noise_ppm * 1e-6)

    # Single-conversion V_ref reads (navg=1) so we see the per-sample current
    # noise rather than averaging it away.
    v_series = {ch: [] for ch in config.channels}
    with transport, Recorder("stage8_crd_noise", config, out_dir=args.out_dir,
                             device_info=board.device_info(),
                             conditions=f"CRD noise: {args.samples} single V_ref conversions/ch") as rec:
        board.configure()
        common.confirm("all channels powered and steady (CRD regulating)", args)
        for _ in range(args.samples):
            for ch in config.channels:
                vref = board.ads.read_vref(ch, n_avg=1)
                v_series[ch].append(vref)
                rec.log(ch, ads_addr=config.ads_map[ch].addr_hex, v_ref=vref, note="CRD noise sample")

    rows = []
    floor = args.floor_ppm * 1e-6
    for ch in config.channels:
        st = noise_stats(np.array(v_series[ch]))
        frac = (st.std / st.mean) if st.mean else float("inf")
        ok = frac <= floor
        gate.record(f"ch{ch} CRD noise below floor", ok,
                    f"{frac*1e6:.1f} ppm rms <= {args.floor_ppm:g} ppm")
        rows.append([ch, f"{st.mean*1e3:.3f}", f"{st.std*1e6:.3f}", f"{frac*1e6:.1f}"])

    report = StageReport(
        stage_name="Stage 8 — CRD noise check",
        objective=("Bound the CRD current noise -- the one source weakness -- by measuring "
                   "fractional V_ref noise over a scan (TESTING_PLAN Part 2 Stage 8)."),
        setup=f"All channels powered, CRD regulating; single-shot V_ref reads. {config.summary()}",
        method=(f"Take {args.samples} single ADS1115 conversions per channel; compute fractional "
                "V_ref noise std/mean (= fractional current noise)."),
        results_intro=f"Floor ±{args.floor_ppm:g} ppm rms fractional current noise.",
        results_table=markdown_table(
            ["Ch", "V_ref mean [mV]", "V_ref noise [uV]", "Frac noise [ppm]"], rows),
        passed=gate.passed,
        criterion=f"Fractional V_ref (current) noise <= {args.floor_ppm:g} ppm rms on every channel.",
        margin="CRD quiet enough" if gate.passed else "CRD noise exceeds floor",
        next_action="Bring-up complete; archive data and compare against the SPICE noise budget.",
    )
    return common.finish(report, args, gate)


if __name__ == "__main__":
    raise SystemExit(main())