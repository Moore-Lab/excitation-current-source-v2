"""Hardware-free mock of the board + T7, for dry-runs and CI.

Simulates the physical unit cell (board_spec.md sec.1): each channel carries a
current ``I`` through R_ref (top) and the RTD (bottom, Kelvin-sensed). Given a
per-channel scenario (RTD resistance, actual current, R_ref) it returns the same
AIN voltages a real T7 would, so every stage script runs end-to-end with no
hardware. Noise is configurable per channel, which lets Stage 6 exercise both a
**position-independent** board (the design goal) and a synthetic
**series-chain** board (noise growing up the chain) for the comparison tooling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import numpy as np

from config.board_config import (
    BoardConfig,
    DEFAULT_CONFIG,
    Q_SENSEN,
    Q_SENSEP,
    Q_TOP,
    Q_VREF,
    Q_VRTD,
)
from lib.rtd import resistance_from_temp


@dataclass
class ChannelState:
    """Physical truth for one channel that the mock turns into AIN voltages."""

    r_rtd_ohms: float
    current_a: float
    r_ref_ohms: float
    excess_noise_v: float = 0.0  # extra white noise (series-chain emulation)
    fault: str = ""              # "", "open", "shorted_rtd"


def default_adc_noise_v(config: BoardConfig) -> float:
    """A representative T7 white-noise floor for the configured range.

    ~3 uV rms on +/-0.1 V, ~30 uV on +/-1 V -- order-of-magnitude correct for
    the high-resolution-index reads the stages request. Tunable per run.
    """
    return config.ain_range_v * 3e-5


def make_scenario(
    config: BoardConfig = DEFAULT_CONFIG,
    temps_c: Optional[Sequence[float]] = None,
    current_spread: float = 0.004,
    r_ref_tol: float = 5e-5,
    seed: int = 0,
) -> Dict[int, ChannelState]:
    """Build a plausible per-channel truth: distinct temps, small I spread.

    The current spread is what Stage 2 calibration captures; the R_ref tolerance
    is what ratiometric mode rejects. Noise is identical across channels
    (position-independent) -- the board's design goal.
    """
    rng = np.random.default_rng(seed)
    if temps_c is None:
        lo, hi = config.temp_range_c
        # spread channels across the operating band so reports show variety
        temps_c = list(np.linspace(lo + 0.2 * (hi - lo), hi - 0.2 * (hi - lo), config.n_channels))
    states: Dict[int, ChannelState] = {}
    for ch in config.channels:
        t = temps_c[ch] if ch < len(temps_c) else 25.0
        r_rtd = resistance_from_temp(float(t), config.r0_ohms)
        i_ch = config.excitation_current_a * (1.0 + current_spread * rng.standard_normal())
        r_ref = config.r_ref_ohms * (1.0 + r_ref_tol * rng.standard_normal())
        states[ch] = ChannelState(r_rtd_ohms=r_rtd, current_a=i_ch, r_ref_ohms=r_ref)
    return states


def series_chain_scenario(
    config: BoardConfig = DEFAULT_CONFIG,
    base_noise_v: float = 2e-6,
    per_channel_growth_v: float = 6e-6,
    seed: int = 1,
) -> Dict[int, ChannelState]:
    """A synthetic *old* board whose noise grows up the chain (position-dependent).

    Used to fabricate a baseline dataset Stage 6 can compare the new board
    against. Not representative of the REF200 design.
    """
    states = make_scenario(config, seed=seed)
    for ch, st in states.items():
        st.excess_noise_v = base_noise_v + per_channel_growth_v * ch
    return states


class MockT7Backend:
    """Register-level mock matching the T7Backend interface."""

    def __init__(
        self,
        config: BoardConfig = DEFAULT_CONFIG,
        scenario: Optional[Dict[int, ChannelState]] = None,
        seed: int = 12345,
        adc_noise_v: Optional[float] = None,
    ):
        self.config = config
        self.scenario = scenario if scenario is not None else make_scenario(config)
        self.adc_noise_v = adc_noise_v if adc_noise_v is not None else default_adc_noise_v(config)
        self._rng = np.random.default_rng(seed)
        self._registers: Dict[str, float] = {}
        self._rev = config.reverse_lookup()

    # ---- noiseless physics ----------------------------------------------
    def _node_voltage(self, ch: int, quantity: str) -> float:
        st = self.scenario[ch]
        i = st.current_a
        if st.fault == "open":
            return self.config.ain_range_v  # railed -> compliance failure
        r_rtd = 0.0 if st.fault == "shorted_rtd" else st.r_rtd_ohms
        if quantity == Q_VREF:
            return i * st.r_ref_ohms
        if quantity == Q_VRTD:
            return i * r_rtd
        if quantity == Q_TOP:
            return i * (st.r_ref_ohms + r_rtd)
        if quantity == Q_SENSEP:
            return i * r_rtd
        if quantity == Q_SENSEN:
            return 0.0
        raise ValueError(f"unknown quantity {quantity!r}")

    def _read_ain(self, name: str) -> float:
        ch, quantity = self._rev[name]
        base = self._node_voltage(ch, quantity)
        sigma = float(np.hypot(self.adc_noise_v, self.scenario[ch].excess_noise_v))
        v = base + sigma * self._rng.standard_normal()
        rng = self.config.ain_range_v
        return float(np.clip(v, -rng, rng))  # ADC rails at the configured range

    # ---- T7Backend surface ----------------------------------------------
    def write_name(self, name: str, value: float) -> None:
        self._registers[name] = float(value)

    def write_names(self, names: Sequence[str], values: Sequence[float]) -> None:
        for n, v in zip(names, values):
            self.write_name(n, v)

    def read_name(self, name: str) -> float:
        if name in self._rev:
            return self._read_ain(name)
        return self._registers.get(name, 0.0)

    def read_names(self, names: Sequence[str]) -> List[float]:
        return [self.read_name(n) for n in names]

    def info(self) -> Dict[str, object]:
        return {
            "backend": "mock",
            "device_name": "T7-MOCK",
            "serial": 0,
            "firmware": 0.0,
            "config": self.config.summary(),
        }

    def close(self) -> None:
        pass

    def __enter__(self) -> "MockT7Backend":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()