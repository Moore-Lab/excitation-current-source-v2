"""Shared scaffolding for the stage scripts: CLI, board build, gates, prompts.

Every stage imports this so they share one argument surface and one notion of
"gate passed / failed". In ``--mock`` (default) the manual checks auto-confirm so
the whole suite is a hardware-free dry run; on the bench, drop ``--mock`` and the
operator is prompted for the physical checks.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config.board_config import (
    DEFAULT_CONFIG,
    MODE_CAL_CURRENT,
    MODE_FULL_DIFF,
    MODE_SE_SUBTRACT,
    BoardConfig,
    make_config,
)
from lib.paths import DATA_DIR, REPORT_DIR
from t7.backend import T7Backend, get_backend
from t7.board import BoardSession


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def build_arg_parser(description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    conn = p.add_mutually_exclusive_group()
    conn.add_argument("--mock", dest="mock", action="store_true", default=True,
                      help="use the hardware-free mock backend (default)")
    conn.add_argument("--real", dest="mock", action="store_false",
                      help="connect to a real T7 over LJM")
    p.add_argument("--identifier", default="ANY", help="LJM device id (serial/IP/ANY)")

    p.add_argument("--rtd", default=DEFAULT_CONFIG.rtd_type, choices=["Pt100", "Pt1000"],
                   help="RTD type (sets R0, default current/R_ref/range)")
    p.add_argument("--channels", type=int, default=DEFAULT_CONFIG.n_channels)
    p.add_argument("--mode", default=DEFAULT_CONFIG.measurement_mode,
                   choices=[MODE_FULL_DIFF, MODE_SE_SUBTRACT, MODE_CAL_CURRENT])
    p.add_argument("--current-ua", type=float, default=None,
                   help="override excitation current in microamps")
    p.add_argument("--rref", type=float, default=None, help="override R_ref in ohms")
    p.add_argument("--range", type=float, default=None, help="override AIN +/- range in volts")
    p.add_argument("--resolution-index", type=int, default=DEFAULT_CONFIG.resolution_index)
    p.add_argument("--settling-us", type=float, default=DEFAULT_CONFIG.settling_us)

    p.add_argument("--navg", type=int, default=8, help="scans averaged per reading")
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
                   help="known substitution resistance (ohm) for Stage 3/compliance")

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
        measurement_mode=args.mode,
        ain_range_v=args.range,
        resolution_index=args.resolution_index,
        settling_us=args.settling_us,
    )


def _mock_scenario(args: argparse.Namespace, config: BoardConfig):
    from t7.mock_backend import make_scenario, series_chain_scenario

    temps = None
    if args.temps:
        temps = [float(x) for x in args.temps.split(",")]
    if args.scenario == "series_chain":
        return series_chain_scenario(config, seed=args.seed)
    return make_scenario(config, temps_c=temps, seed=args.seed)


def make_board(args: argparse.Namespace, config: BoardConfig) -> Tuple[T7Backend, BoardSession]:
    if args.mock:
        scenario = _mock_scenario(args, config)
        backend = get_backend(mock=True, config=config, scenario=scenario, seed=args.seed)
    else:
        backend = get_backend(mock=False, identifier=args.identifier)
    board = BoardSession(backend, config)
    return backend, board


def mock_backend(board: BoardSession):
    """Return the MockT7Backend behind a board, or None on real hardware.

    Stages use this only to inject the physical truth a bench operator would set
    by hand (decade-box value, RTD temperature, channel perturbation) so the
    same script drives both the mock and the real board.
    """
    from t7.mock_backend import MockT7Backend

    return board.backend if isinstance(board.backend, MockT7Backend) else None


def set_mock_rtd(board: BoardSession, r_ohms: float, channels=None) -> None:
    """In --mock, set the simulated RTD resistance (substitution / temp set)."""
    mb = mock_backend(board)
    if mb is None:
        return
    for ch in (channels if channels is not None else board.config.channels):
        mb.scenario[ch].r_rtd_ohms = r_ohms


def mock_truth_current(board: BoardSession, ch: int):
    """The simulated true current for a channel (Stage 2 DMM stand-in), or None."""
    mb = mock_backend(board)
    return None if mb is None else mb.scenario[ch].current_a


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