"""Canonical filesystem locations for the bench tooling.

Track C owns ``test/**`` and (for generated output) ``reports/test/``. These
helpers resolve those relative to the repo so scripts work from any CWD.
"""

from __future__ import annotations

from pathlib import Path

TEST_DIR = Path(__file__).resolve().parents[1]   # .../test
REPO_ROOT = TEST_DIR.parent                       # repo root
DATA_DIR = TEST_DIR / "data"                       # committed measured data
BASELINE_DIR = DATA_DIR / "baselines"              # reference datasets (e.g. old board)
REPORT_DIR = REPO_ROOT / "reports" / "test"        # generated stage reports
CALIB_PATH = DATA_DIR / "calibration.json"         # per-channel current constants


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path