"""Canonical filesystem locations, resolved relative to the repo.

``host/`` is the acquisition library; the bench tooling in ``test/`` writes
measured data to ``test/data/`` and generated reports to ``reports/test/``
(DIRECTORY_MANAGEMENT.md). These helpers locate those dirs from any CWD so the
stage scripts and the persisted cross-cal file work regardless of where they run.
"""

from __future__ import annotations

from pathlib import Path

HOST_DIR = Path(__file__).resolve().parent          # .../host
REPO_ROOT = HOST_DIR.parent                          # repo root
TEST_DIR = REPO_ROOT / "test"
DATA_DIR = TEST_DIR / "data"                         # committed measured data
BASELINE_DIR = DATA_DIR / "baselines"                # old series-chain datasets
REPORT_DIR = REPO_ROOT / "reports" / "test"          # generated stage reports
CALIB_PATH = DATA_DIR / "cross_cal.json"             # per-channel constant C


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
