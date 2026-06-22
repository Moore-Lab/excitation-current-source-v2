"""Measured-data logging (CSV + JSON metadata sidecar).

Raw bench data is irreplaceable and committed (``test/data/``,
DIRECTORY_MANAGEMENT.md). Every run writes:
  - ``<stage>_<runid>.csv``       : one row per sample, fixed schema
  - ``<stage>_<runid>.meta.json`` : run provenance (config, device, conditions)

The CSV schema is stable across stages and versions so any reader -- and the old
series-chain baseline -- loads the same way.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, Optional

import numpy as np

from host.config import BoardConfig
from host.paths import DATA_DIR, ensure_dir

# Canonical column order. Stages write the subset that applies; missing values
# are left blank so every file shares one header.
SCHEMA: List[str] = [
    "iso_time",      # absolute UTC timestamp
    "t_rel_s",       # seconds since run start
    "stage",
    "channel",
    "ads_addr",      # ADS1115 I²C address that produced V_ref (e.g. 0x48)
    "v_ref",         # volts across R_ref (ADS1115)
    "v_rtd",         # volts across the RTD, Kelvin (T7)
    "ratio",         # V_RTD / V_ref
    "c_const",       # per-channel cross-cal constant C used (ohm)
    "r_calc",        # recovered RTD resistance (ohm)
    "t_calc",        # recovered temperature (degC)
    "r_known",       # known/reference R for substitution stages (ohm)
    "note",
]


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


class Recorder:
    """Append-style CSV writer with a metadata sidecar."""

    def __init__(
        self,
        stage: str,
        config: BoardConfig,
        out_dir: Path = DATA_DIR,
        run_id: Optional[str] = None,
        device_info: Optional[Mapping[str, object]] = None,
        conditions: str = "",
    ):
        self.stage = stage
        self.config = config
        self.run_id = run_id or new_run_id()
        ensure_dir(out_dir)
        self.csv_path = out_dir / f"{stage}_{self.run_id}.csv"
        self.meta_path = out_dir / f"{stage}_{self.run_id}.meta.json"
        self._t0 = datetime.now(timezone.utc)
        self._fh = self.csv_path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._fh, fieldnames=SCHEMA, extrasaction="ignore")
        self._writer.writeheader()
        self._rows = 0
        self._write_meta(device_info, conditions)

    def _write_meta(self, device_info, conditions) -> None:
        meta = {
            "schema": "rtd-bench/1",
            "stage": self.stage,
            "run_id": self.run_id,
            "started_utc": self._t0.isoformat(timespec="seconds"),
            "config": self.config.summary(),
            "rtd_type": self.config.rtd_type,
            "n_channels": self.config.n_channels,
            "ads_addresses": [f"0x{a:02X}" for a in self.config.ads_addresses],
            "device": dict(device_info) if device_info else {},
            "conditions": conditions,
            "csv": self.csv_path.name,
            "columns": SCHEMA,
        }
        self.meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    def log(self, channel: int, **fields) -> None:
        now = datetime.now(timezone.utc)
        row = {
            "iso_time": now.isoformat(timespec="milliseconds"),
            "t_rel_s": round((now - self._t0).total_seconds(), 6),
            "stage": self.stage,
            "channel": channel,
        }
        row.update(fields)
        self._writer.writerow(row)
        self._rows += 1

    @property
    def rows(self) -> int:
        return self._rows

    def close(self) -> None:
        if not self._fh.closed:
            self._fh.flush()
            self._fh.close()

    def __enter__(self) -> "Recorder":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def load_run(csv_path: Path) -> Dict[str, np.ndarray]:
    """Load a logged CSV into column arrays (floats where possible)."""
    with Path(csv_path).open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        cols: Dict[str, List[str]] = {name: [] for name in (reader.fieldnames or [])}
        for row in reader:
            for k, v in row.items():
                cols[k].append(v)
    out: Dict[str, np.ndarray] = {}
    for name, vals in cols.items():
        try:
            out[name] = np.array([float(v) if v != "" else np.nan for v in vals])
        except ValueError:
            out[name] = np.array(vals, dtype=object)
    return out


def channel_series(csv_path: Path, column: str, channel: int) -> np.ndarray:
    """Extract one column for one channel from a logged run (drops NaNs)."""
    data = load_run(csv_path)
    chan = data["channel"].astype(float)
    vals = data[column].astype(float)
    sel = vals[chan == channel]
    return sel[~np.isnan(sel)]
