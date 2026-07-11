"""T7 driver: reads V_RTD on the existing differential pairs.

Each RTD's Kelvin sense pair lands on one T7 differential input (config maps
channel -> AIN{2ch}/AIN{2ch+1}). This driver sets the range, resolution index,
settling time and negative-channel pairing once, then returns per-channel V_RTD.

Range follows the RTD type (board_spec.md "RTD voltage"): ±0.1 V for Pt100
(≈19–38 mV at ~240 µA), ±1 V for Pt1000. A high resolution index and adequate
settling guard the mux-settling risk -- each channel must fully settle within
its dwell before the next is read.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np

from host.config import BoardConfig
from host.transport import Transport


class T7RTDReader:
    def __init__(self, transport: Transport, config: BoardConfig):
        self.transport = transport
        self.config = config

    def configure_inputs(self) -> None:
        """Set range / resolution / settling / negative-channel on every V_RTD pair."""
        names: List[str] = []
        values: List[float] = []
        for ch in self.config.channels:
            pin = self.config.t7_map[ch]
            names += [
                f"AIN{pin.pos}_RANGE",
                f"AIN{pin.pos}_RESOLUTION_INDEX",
                f"AIN{pin.pos}_SETTLING_US",
                f"AIN{pin.pos}_NEGATIVE_CH",
            ]
            values += [
                self.config.t7_range_v,
                float(self.config.t7_resolution_index),
                float(self.config.t7_settling_us),
                float(pin.neg),
            ]
        self.transport.write_register(names, values)

    def read_vrtd_all(self, n_avg: int = 1) -> Dict[int, float]:
        """Per-channel V_RTD (volts), software-averaged over ``n_avg`` whole scans.

        Software averaging stacks on top of the T7's own resolution averaging --
        the cheap SNR recovery for the small ~20–35 mV Pt100 signal.
        """
        names = self.config.t7_read_names()
        acc = np.zeros(len(names))
        for _ in range(max(1, n_avg)):
            acc += np.asarray(self.transport.read_analog(names), dtype=float)
        acc /= max(1, n_avg)
        return {ch: float(v) for ch, v in zip(self.config.channels, acc)}

    def read_vrtd(self, ch: int, n_avg: int = 1) -> float:
        """V_RTD for a single channel (averaged)."""
        name = self.config.t7_map[ch].read_name
        acc = 0.0
        for _ in range(max(1, n_avg)):
            acc += float(self.transport.read_analog([name])[0])
        return acc / max(1, n_avg)
