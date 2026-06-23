"""Per-channel cross-calibration constant C (Stage 2 output).

Stage 2 substitutes a known resistor for each RTD and computes
``C = R_known·(V_ref/V_RTD)``; this module persists those constants. Stages 3–8
load them back to recover ``R = C·V_RTD/V_ref``. JSON so it diffs cleanly and is
human-auditable, with provenance (the R_known used, the converter ranges, the
date) because C is only valid until the next recalibration (board_spec.md: C
drifts with R_ref tempco + relative ADC gain tempco).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from host.config import BoardConfig
from host.paths import CALIB_PATH, ensure_dir


def save_cross_cal(
    constants: Dict[int, float],
    config: BoardConfig,
    r_known_ohms: float,
    path: Path = CALIB_PATH,
    notes: str = "",
    instrument: str = "",
) -> Path:
    """Write per-channel C (channel -> ohms) with provenance metadata."""
    ensure_dir(path.parent)
    payload = {
        "schema": "rtd-crosscal/1",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rtd_type": config.rtd_type,
        "n_channels": config.n_channels,
        "r_known_ohms": float(r_known_ohms),
        "t7_range_v": config.t7_range_v,
        "ads_range_v": config.ads_range_v,
        "config": config.summary(),
        "instrument": instrument,
        "notes": notes,
        "c_ohms": {str(ch): float(c) for ch, c in sorted(constants.items())},
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_cross_cal(path: Path = CALIB_PATH) -> Dict[int, float]:
    """Return channel -> C (ohms). Raises if the file is absent."""
    if not path.exists():
        raise FileNotFoundError(
            f"no cross-calibration at {path}. Run Stage 2 (cross-calibration) first."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return {int(ch): float(c) for ch, c in data["c_ohms"].items()}


def try_load_cross_cal(path: Path = CALIB_PATH) -> Optional[Dict[int, float]]:
    try:
        return load_cross_cal(path)
    except FileNotFoundError:
        return None
