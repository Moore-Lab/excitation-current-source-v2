"""BoardSession: applies the AIN map to a T7 backend.

This is the layer the stage scripts use: it configures each AIN's range,
resolution, settling and differential/SE pairing once, then exposes per-channel
voltage reads. It collapses the three measurement modes (full-diff, SE-subtract,
calibrated-current) into a uniform ``{Q_VREF, Q_VRTD}`` result so the stages and
the measurement math don't branch on mode.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from config.board_config import (
    BoardConfig,
    MODE_SE_SUBTRACT,
    Q_SENSEN,
    Q_SENSEP,
    Q_TOP,
    Q_VREF,
    Q_VRTD,
)
from t7.backend import T7Backend


class BoardSession:
    def __init__(self, backend: T7Backend, config: BoardConfig):
        self.backend = backend
        self.config = config

    # ---- configuration ---------------------------------------------------
    def configure_inputs(self) -> None:
        """Set range / resolution / settling / negative-channel on every AIN.

        Settling and resolution index guard the mux-settling risk
        (board_spec.md sec.6): each channel must fully settle within its dwell.
        """
        names: List[str] = []
        values: List[float] = []
        for _ch, pin in self.config.all_pins():
            p = pin.pos
            names += [
                f"AIN{p}_RANGE",
                f"AIN{p}_RESOLUTION_INDEX",
                f"AIN{p}_SETTLING_US",
                f"AIN{p}_NEGATIVE_CH",
            ]
            values += [
                self.config.ain_range_v,
                float(self.config.resolution_index),
                float(self.config.settling_us),
                float(pin.negative_ch),
            ]
        self.backend.write_names(names, values)

    # ---- raw pin reads ---------------------------------------------------
    def read_pins(self, n_avg: int = 1) -> Dict[int, Dict[str, float]]:
        """Read every configured pin; return ch -> {quantity: volts}.

        n_avg software-averages whole scans (on top of the T7's own resolution
        averaging) -- the easy SNR recovery for the 100 uA / 10 mV operating
        point noted in the spec deviation.
        """
        names = self.config.read_names()
        acc = np.zeros(len(names))
        for _ in range(max(1, n_avg)):
            acc += np.asarray(self.backend.read_names(names), dtype=float)
        acc /= max(1, n_avg)

        out: Dict[int, Dict[str, float]] = {ch: {} for ch in self.config.channels}
        for (ch, pin), val in zip(self.config.all_pins(), acc):
            out[ch][pin.quantity] = float(val)
        return out

    # ---- collapsed per-channel voltages ----------------------------------
    def read_voltages(self, n_avg: int = 1) -> Dict[int, Dict[str, float]]:
        """Per-channel {Q_VREF, Q_VRTD} (V_ref omitted in calibrated-current).

        SE-subtract is collapsed in software: V_ref = TOP - Sense+,
        V_RTD = Sense+ - Sense- (board_spec.md sec.5).
        """
        raw = self.read_pins(n_avg=n_avg)
        out: Dict[int, Dict[str, float]] = {}
        for ch, q in raw.items():
            if self.config.measurement_mode == MODE_SE_SUBTRACT:
                out[ch] = {
                    Q_VREF: q[Q_TOP] - q[Q_SENSEP],
                    Q_VRTD: q[Q_SENSEP] - q[Q_SENSEN],
                }
            else:
                collapsed = {Q_VRTD: q[Q_VRTD]}
                if Q_VREF in q:
                    collapsed[Q_VREF] = q[Q_VREF]
                out[ch] = collapsed
        return out

    # ---- noise sampling --------------------------------------------------
    def sample_voltage(
        self, ch: int, quantity: str, n_samples: int, n_avg: int = 1
    ) -> np.ndarray:
        """Time series of one channel/quantity for noise + drift analysis."""
        data = np.empty(n_samples)
        for i in range(n_samples):
            data[i] = self.read_voltages(n_avg=n_avg)[ch][quantity]
        return data

    def device_info(self) -> Dict[str, object]:
        return self.backend.info()