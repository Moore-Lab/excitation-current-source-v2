"""Shared scaffolding for the stage scripts: CLI, board build, gates, prompts.

Every stage imports this so they share one argument surface and one notion of
"gate passed / failed". In ``--mock`` (default) the manual checks auto-confirm so
the whole suite is a hardware-free dry run; on the bench, drop ``--mock`` and the
operator is prompted for the physical checks and instrument entries.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from host.acquire import BoardSession
from host.config import DEFAULT_CONFIG, BoardConfig, Q_VREF, Q_VRTD, make_config
from host.calibration import save_cross_cal, try_load_cross_cal
from host.measurement import cross_cal_constant
from host.paths import DATA_DIR, REPORT_DIR
from host.rtd import resistance_from_temp
from host.transport import Transport, get_transport

# Stage output (rail symbols ±, Ω, °, I²C, …) is UTF-8; make sure a legacy
# console encoding (e.g. Windows cp1252) degrades gracefully instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # pytest capture / already-wrapped streams
        pass


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def build_arg_parser(description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    conn = p.add_mutually_exclusive_group()
    conn.add_argument("--mock", dest="mock", action="store_true", default=True,
                      help="use the hardware-free mock transport (default)")
    conn.add_argument("--real", dest="mock", action="store_false",
                      help="connect to a real T7 over LJM")
    p.add_argument("--identifier", default="ANY", help="LJM device id (serial/IP/ANY)")

    p.add_argument("--rtd", default=DEFAULT_CONFIG.rtd_type, choices=["Pt100", "Pt1000"],
                   help="RTD type (sets R0 and the default T7 range)")
    p.add_argument("--channels", type=int, default=DEFAULT_CONFIG.n_channels)
    p.add_argument("--current-ua", type=float, default=None,
                   help="override nominal CRD current in microamps")
    p.add_argument("--rref", type=float, default=None, help="override R_ref in ohms")
    # T7 (V_RTD) acquisition
    p.add_argument("--t7-range", type=float, default=None, help="T7 AIN ± range (V)")
    p.add_argument("--resolution-index", type=int, default=DEFAULT_CONFIG.t7_resolution_index)
    p.add_argument("--settling-us", type=float, default=DEFAULT_CONFIG.t7_settling_us)
    p.add_argument("--navg", type=int, default=8, help="T7 scans averaged per V_RTD reading")
    # ADS1115 (V_ref) acquisition
    p.add_argument("--ads-range", type=float, default=DEFAULT_CONFIG.ads_range_v,
                   help="ADS1115 PGA ± full-scale (V); default ±0.256")
    p.add_argument("--ads-rate", type=int, default=DEFAULT_CONFIG.ads_data_rate_sps,
                   help="ADS1115 data rate (SPS)")
    p.add_argument("--ads-navg", type=int, default=DEFAULT_CONFIG.ads_navg,
                   help="ADS1115 conversions averaged per V_ref reading")

    p.add_argument("--samples", type=int, default=64, help="samples for noise/soak stages")
    p.add_argument("--interval-s", type=float, default=0.0,
                   help="delay between samples (0 = as fast as possible)")

    # mock scenario controls
    p.add_argument("--scenario", default="nominal", choices=["nominal", "series_chain"],
                   help="mock board behaviour")
    p.add_argument("--seed", type=int, default=12345)
    p.add_argument("--temps", default=None,
                   help="comma-separated per-channel temps (degC) for the mock")
    p.add_argument("--known-r", type=float, default=None,
                   help="known substitution resistance (ohm) for cross-cal / sweeps")

    # output
    p.add_argument("--out-dir", type=Path, default=DATA_DIR, help="data output dir")
    p.add_argument("--report-dir", type=Path, default=REPORT_DIR, help="report output dir")
    p.add_argument("--no-report", action="store_true", help="skip writing the report")
    p.add_argument("--yes", action="store_true",
                   help="auto-confirm manual checks (implied in --mock)")
    return p


def config_from_args(args: argparse.Namespace) -> BoardConfig:
    current = (args.current_ua * 1e-6) if args.current_ua is not None else None
    return make_config(
        rtd_type=args.rtd,
        n_channels=args.channels,
        excitation_current_a=current,
        r_ref_ohms=args.rref,
        t7_range_v=args.t7_range,
        t7_resolution_index=args.resolution_index,
        t7_settling_us=args.settling_us,
        ads_range_v=args.ads_range,
        ads_data_rate_sps=args.ads_rate,
        ads_navg=args.ads_navg,
    )


def _mock_scenario(args: argparse.Namespace, config: BoardConfig):
    from host.transport import make_scenario, series_chain_scenario

    temps = [float(x) for x in args.temps.split(",")] if args.temps else None
    if args.scenario == "series_chain":
        return series_chain_scenario(config, seed=args.seed)
    return make_scenario(config, temps_c=temps, seed=args.seed)


def make_board(args: argparse.Namespace, config: BoardConfig) -> Tuple[Transport, BoardSession]:
    if args.mock:
        scenario = _mock_scenario(args, config)
        transport = get_transport(mock=True, config=config, scenario=scenario, seed=args.seed)
    else:
        transport = get_transport(mock=False, identifier=args.identifier)
    return transport, BoardSession(transport, config)


def mock_transport(board: BoardSession):
    """Return the MockTransport behind a board, or None on real hardware.

    Stages use this only to inject the physical truth a bench operator would set
    by hand (decade-box value, RTD temperature, channel perturbation) so the
    same script drives both the mock and the real board.
    """
    from host.transport import MockTransport

    return board.transport if isinstance(board.transport, MockTransport) else None


def set_mock_rtd(board: BoardSession, r_ohms: float, channels=None) -> None:
    """In --mock, set the simulated RTD resistance (substitution / temperature set)."""
    mt = mock_transport(board)
    if mt is None:
        return
    for ch in (channels if channels is not None else board.config.channels):
        mt.scenario[ch].r_rtd_ohms = r_ohms


def set_mock_crd_noise(board: BoardSession, frac: float, channels=None) -> None:
    """In --mock, set the simulated fractional CRD current noise (Stage 8)."""
    mt = mock_transport(board)
    if mt is None:
        return
    for ch in (channels if channels is not None else board.config.channels):
        mt.scenario[ch].crd_noise_frac = frac


def calib_path(args: argparse.Namespace) -> Path:
    return args.out_dir / "cross_cal.json"


def load_or_make_cross_cal(
    board: BoardSession, args: argparse.Namespace, config: BoardConfig
) -> Dict[int, float]:
    """Return per-channel C, computing it in-situ if no Stage-2 file exists.

    On the bench the real cross-cal file (Stage 2) is authoritative. For a
    hardware-free dry run of a downstream stage in isolation, bootstrap C by
    cross-calibrating against a known resistor so the stage is still runnable.
    """
    existing = try_load_cross_cal(calib_path(args))
    if existing:
        return existing
    if not args.mock:
        raise FileNotFoundError(
            f"no cross-calibration at {calib_path(args)}. Run Stage 2 first."
        )
    r_known = args.known_r if args.known_r is not None else config.r0_ohms
    set_mock_rtd(board, r_known)
    constants: Dict[int, float] = {}
    for ch in config.channels:
        v = board.read_channel(ch, t7_navg=max(8, args.navg), ads_navg=config.ads_navg)
        constants[ch] = cross_cal_constant(r_known, v[Q_VRTD], v[Q_VREF])
    save_cross_cal(constants, config, r_known, path=calib_path(args),
                   instrument="(auto-bootstrap, mock dry-run)",
                   notes="synthetic C for standalone dry run; replaced by Stage 2 on the bench")
    return constants


# --------------------------------------------------------------------------
# Gates and operator prompts
# --------------------------------------------------------------------------
@dataclass
class Gate:
    name: str
    passed: bool
    detail: str = ""


class GateLog:
    """Collects go/no-go results; a stage is PASS only if every gate passes."""

    def __init__(self, stage: str):
        self.stage = stage
        self.gates: List[Gate] = []

    def record(self, name: str, passed: bool, detail: str = "") -> bool:
        self.gates.append(Gate(name, passed, detail))
        mark = "PASS" if passed else "FAIL"
        print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))
        return passed

    @property
    def passed(self) -> bool:
        return all(g.passed for g in self.gates) and len(self.gates) > 0

    def table_rows(self) -> List[List[object]]:
        return [[g.name, "PASS" if g.passed else "FAIL", g.detail] for g in self.gates]


def auto(args: argparse.Namespace) -> bool:
    """True when manual checks should auto-confirm (mock or --yes)."""
    return bool(args.mock or args.yes)


def confirm(prompt: str, args: argparse.Namespace, auto_value: bool = True) -> bool:
    """Operator y/n confirmation; auto-answers in mock/--yes/non-interactive."""
    if auto(args) or not sys.stdin.isatty():
        print(f"  ? {prompt} -> auto:{'yes' if auto_value else 'no'}")
        return auto_value
    resp = input(f"  ? {prompt} [y/N]: ").strip().lower()
    return resp in ("y", "yes")


def ask_float(prompt: str, args: argparse.Namespace, auto_value: float) -> float:
    """Numeric operator entry; auto-returns the supplied value in mock mode."""
    if auto(args) or not sys.stdin.isatty():
        print(f"  ? {prompt} -> auto:{auto_value:g}")
        return auto_value
    while True:
        raw = input(f"  ? {prompt} [{auto_value:g}]: ").strip()
        if raw == "":
            return auto_value
        try:
            return float(raw)
        except ValueError:
            print("    not a number, try again")


def header(stage_title: str, config: BoardConfig, args: argparse.Namespace) -> None:
    print("=" * 72)
    print(stage_title)
    print(f"  config : {config.summary()}")
    print(f"  backend: {'MOCK' if args.mock else 'REAL T7 (LJM)'}  scenario={args.scenario}")
    print("=" * 72)


def finish(report, args: argparse.Namespace, gate: GateLog) -> int:
    """Write the report (unless suppressed) and return a process exit code."""
    if not args.no_report:
        path = report.write(out_dir=args.report_dir)
        print(f"\nreport: {path}")
    status = "PASS" if gate.passed else "FAIL"
    print(f"STAGE {status}: {gate.stage}")
    return 0 if gate.passed else 1


# Re-export for stages that build a board and immediately read constants.
__all__ = [
    "build_arg_parser", "config_from_args", "make_board", "mock_transport",
    "set_mock_rtd", "set_mock_crd_noise", "calib_path", "load_or_make_cross_cal",
    "Gate", "GateLog", "auto", "confirm", "ask_float", "header", "finish",
    "resistance_from_temp", "Q_VREF", "Q_VRTD",
]
