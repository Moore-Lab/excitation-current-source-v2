"""BoardSession: the time-aligned dual-ADC read.

Ties the two drivers together. Per channel it reads V_RTD on the T7 and V_ref on
the ADS1115 close in time and returns a uniform ``{Q_VRTD, Q_VREF}`` so the
measurement math and the stages never branch on which converter produced what.

The excitation current is steady over a scan (a CRD), so modest T7↔ADS skew is
harmless -- but the read is still *structured* per channel (both quantities
back-to-back before advancing) so the ratio uses the closest-in-time pair, which
keeps any slow current drift common-mode and cancelled in V_RTD/V_ref.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np

from host.ads1115 import ADS1115Array
from host.config import BoardConfig, Q_VREF, Q_VRTD
from host.t7_rtd import T7RTDReader
from host.transport import Transport


class BoardSession:
    def __init__(self, transport: Transport, config: BoardConfig):
        self.transport = transport
        self.config = config
        self.t7 = T7RTDReader(transport, config)
        self.ads = ADS1115Array(transport, config)

    # ---- configuration ---------------------------------------------------
    def configure(self) -> None:
        """Configure both converters (T7 AINs + ADS1115 I²C engine)."""
        self.t7.configure_inputs()
        self.ads.configure()

    def scan_i2c(self) -> List[int]:
        """Addresses of ADS1115 chips that acknowledge on the bus (Stage 1)."""
        return self.ads.scan()

    # ---- reads -----------------------------------------------------------
    def read_channel(self, ch: int, t7_navg: int = 1, ads_navg: int = None) -> Dict[str, float]:
        """Time-aligned {V_RTD, V_ref} for one channel."""
        v_rtd = self.t7.read_vrtd(ch, n_avg=t7_navg)
        v_ref = self.ads.read_vref(ch, n_avg=ads_navg)
        return {Q_VRTD: v_rtd, Q_VREF: v_ref}

    def read_channels(self, t7_navg: int = 1, ads_navg: int = None) -> Dict[int, Dict[str, float]]:
        """Time-aligned {V_RTD, V_ref} for every channel, in scan order."""
        return {ch: self.read_channel(ch, t7_navg=t7_navg, ads_navg=ads_navg)
                for ch in self.config.channels}

    def sample_channel(
        self, ch: int, quantity: str, n_samples: int,
        t7_navg: int = 1, ads_navg: int = None,
    ) -> np.ndarray:
        """Time series of one channel/quantity for noise + drift analysis."""
        data = np.empty(n_samples)
        for i in range(n_samples):
            data[i] = self.read_channel(ch, t7_navg=t7_navg, ads_navg=ads_navg)[quantity]
        return data

    def device_info(self) -> Dict[str, object]:
        return self.transport.info()
