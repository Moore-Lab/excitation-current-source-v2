"""Per-channel current calibration constants (Stage 2 output).

Stage 2 measures each channel's actual delivered current with a DMM / known
resistor and stores it here. Calibrated-current mode (board_spec.md sec.5) reads
it back. JSON so it diffs cleanly and is human-auditable.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from config.board_config import BoardConfig
from lib.paths import CALIB_PATH, ensure_dir


def save_calibration(
    currents_a: Dict[int, float],
    config: BoardConfig,
    path: Path = CALIB_PATH,
    notes: str = "",
    instrument: str = "",
) -> Path:
    """Write per-channel currents (channel -> amps) with provenance metadata."""
    ensure_dir(path.parent)
    payload = {
        "schema": "ref200-calibration/1",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rtd_type": config.rtd_type,
        "n_channels": config.n_channels,
        "nominal_current_a": config.excitation_current_a,
        "config": config.summary(),
        "instrument": instrument,
        "notes": notes,
        "currents_a": {str(ch): float(i) for ch, i in sorted(currents_a.items())},
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_calibration(path: Path = CALIB_PATH) -> Dict[int, float]:
    """Return channel -> current (amps). Raises if the file is absent."""
    if not path.exists():
        raise FileNotFoundError(
            f"no calibration at {path}. Run Stage 2 (current verification) first."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return {int(ch): float(i) for ch, i in data["currents_a"].items()}


def try_load_calibration(path: Path = CALIB_PATH) -> Optional[Dict[int, float]]:
    try:
        return load_calibration(path)
    except FileNotFoundError:
        return None