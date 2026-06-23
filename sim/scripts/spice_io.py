"""
spice_io.py - shared helpers for the RTD-readout SPICE harness (Track B).

  * locate the ngspice console binary (env override -> conda env -> PATH)
  * run a deck headless and capture its log
  * load ngspice `wrdata` output (with or without a vecnames header)
  * a few physical constants and the report skeleton writer

No third-party deps beyond numpy. Paths are all resolved relative to the repo
root so the whole harness is position-independent (run_all enforces cwd=root).
"""
from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np

# --- repo layout -----------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
NETLIST_DIR = REPO_ROOT / "sim" / "netlists"
DATA_DIR = REPO_ROOT / "reports" / "sim" / "data"
LOG_DIR = REPO_ROOT / "reports" / "sim" / "logs"
PLOT_DIR = REPO_ROOT / "reports" / "sim" / "plots"
REPORT_DIR = REPO_ROOT / "reports" / "sim"

# --- physical constants & board references (mirror sim/models/params.inc) ---
KB = 1.380649e-23          # Boltzmann [J/K]
T_KELVIN = 300.15          # ngspice default TNOM/TEMP = 27 C
R_REF = 910.0              # reference resistor [Ohm]
PT100_DRDT = 0.39083       # Pt100 dR/dT at 0 C [Ohm/degC]
PT100_SENS_C = 100.0 / PT100_DRDT   # degC per fractional ratio error (~255.9)
ADS_FS = 0.256             # ADS1115 +/-0.256 V range [V]
ADS_LSB = 7.8125e-6        # ADS1115 LSB on the +/-0.256 V range [V]


def find_ngspice() -> str:
    """Return a path to ngspice's batch/console executable."""
    env = os.environ.get("NGSPICE_BIN")
    if env and Path(env).exists():
        return env
    candidates = [
        Path(os.environ.get("CONDA_PREFIX", "")) / "envs" / "spice" / "Library" / "bin" / "ngspice_con.exe",
        Path.home() / "anaconda3" / "envs" / "spice" / "Library" / "bin" / "ngspice_con.exe",
        Path.home() / "miniconda3" / "envs" / "spice" / "Library" / "bin" / "ngspice_con.exe",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    for name in ("ngspice_con", "ngspice_con.exe", "ngspice", "ngspice.exe"):
        hit = shutil.which(name)
        if hit:
            return hit
    raise FileNotFoundError(
        "ngspice console binary not found. Set NGSPICE_BIN, or create the conda "
        "env:  conda create -y -n spice -c conda-forge ngspice"
    )


def run_deck(deck_name: str, ngspice: str | None = None) -> Path:
    """Run sim/netlists/<deck_name> headless from the repo root; return log path."""
    ng = ngspice or find_ngspice()
    deck = NETLIST_DIR / deck_name
    log = LOG_DIR / (deck.stem + ".log")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # cwd MUST be the repo root: decks use repo-root-relative .include / wrdata.
    subprocess.run([ng, "-b", str(deck), "-o", str(log)],
                   cwd=str(REPO_ROOT), check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return log


def load_wrdata(path: str | Path) -> np.ndarray:
    """Load an ngspice wrdata file -> (rows, cols) float array.

    Tolerates an optional `set wr_vecnames` header line and blank lines by
    skipping any row that does not fully parse as floats.
    """
    rows = []
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        try:
            rows.append([float(p) for p in parts])
        except ValueError:
            continue  # header / vecnames line
    if not rows:
        raise ValueError(f"no numeric rows in {path}")
    return np.array(rows)


def johnson_density(r_ohm: float, t_kelvin: float = T_KELVIN) -> float:
    """Johnson voltage-noise density of a resistor [V/sqrt(Hz)]."""
    return float(np.sqrt(4.0 * KB * t_kelvin * r_ohm))


def write_report(stem: str, title: str, sections: dict[str, str]) -> Path:
    """Write a report following the TESTING_PLAN skeleton. `sections` keys map to
    the fixed headings; missing keys are omitted."""
    order = ["Objective", "Setup", "Method", "Results",
             "Pass / Fail", "Anomalies & notes", "Next"]
    lines = [f"# {title} — 2026-06-22 — sim", ""]
    for key in order:
        if key in sections:
            lines.append(f"## {key}")
            lines.append(sections[key].rstrip())
            lines.append("")
    out = REPORT_DIR / f"{stem}.md"
    out.write_text("\n".join(lines), encoding="utf-8")   # em-dash etc. on GitHub
    return out
