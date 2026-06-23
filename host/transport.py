"""Transport: the single device that does both jobs, plus a hardware-free mock.

On the bench one LabJack T7 Pro carries the whole acquisition: it reads V_RTD on
its analog differential pairs **and** drives the ADS1115 I²C bus on its digital
lines (board_spec.md "Board as the hub"). So the transport exposes two surfaces
behind one connection:

  * analog  -- ``read_analog`` / ``write_register`` (LJM eReadNames/eWriteNames)
  * I²C     -- ``i2c_xfer`` (LJM I2C register block on the same handle)

The drivers (``t7_rtd``, ``ads1115``) talk only to this interface, never to
``labjack.ljm`` directly, so every stage runs with no hardware (``MockTransport``)
and the real path is a drop-in swap. The mock simulates the physical unit cell
*and* models the ADS1115 at the I²C-register level, so the real ADS1115 register
packing/unpacking in ``ads1115.py`` is exercised in dry runs -- not bypassed.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from host.config import (
    ADS_MUX_2_3,
    BoardConfig,
    DEFAULT_CONFIG,
)
from host.rtd import resistance_from_temp

# ADS1115 register pointers and PGA full-scale table (datasheet Table; also used
# by the real driver). Kept here too so the mock can model the chip faithfully.
ADS_REG_CONVERSION = 0x00
ADS_REG_CONFIG = 0x01
ADS_PGA_FS_VOLTS = {
    0b000: 6.144,
    0b001: 4.096,
    0b010: 2.048,
    0b011: 1.024,
    0b100: 0.512,
    0b101: 0.256,
    0b110: 0.256,
    0b111: 0.256,
}


def pga_lsb_volts(pga_field: int) -> float:
    """Volts per LSB for an ADS1115 PGA field (16-bit, ±FS over 2^15)."""
    return ADS_PGA_FS_VOLTS[pga_field] / 32768.0


# ==========================================================================
# Abstract transport
# ==========================================================================
class Transport(ABC):
    """Minimal device interface: analog reads + register writes + I²C xfers."""

    @abstractmethod
    def read_analog(self, names: Sequence[str]) -> List[float]: ...

    @abstractmethod
    def write_register(self, names: Sequence[str], values: Sequence[float]) -> None: ...

    @abstractmethod
    def i2c_config(self, sda_dion: int, scl_dion: int) -> None: ...

    @abstractmethod
    def i2c_xfer(self, address: int, tx: bytes, num_rx: int) -> Tuple[bytes, bool]:
        """Write ``tx`` then read ``num_rx`` bytes from ``address``.

        Returns (rx_bytes, ack) where ``ack`` is True if the slave acknowledged
        (used by the bus scan to detect present chips).
        """

    @abstractmethod
    def info(self) -> Dict[str, object]: ...

    @abstractmethod
    def close(self) -> None: ...

    def __enter__(self) -> "Transport":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def get_transport(mock: bool = True, identifier: str = "ANY", **mock_kwargs) -> Transport:
    """Return a real (LJM) or mock transport. ``mock=True`` is the dry-run default."""
    if mock:
        return MockTransport(**mock_kwargs)
    return LJMTransport(identifier=identifier)


# ==========================================================================
# Real LabJack T7 Pro transport (LJM)
# ==========================================================================
class LJMTransport(Transport):
    """T7 Pro over LJM: eReadNames for V_RTD, the I2C register block for V_ref.

    ``labjack-ljm`` and the LJM runtime are imported lazily so the mock path
    needs neither. Untested against silicon in this repo -- the bench operator
    validates it in Stage 1; the mock mirrors the same call surface.
    """

    def __init__(self, identifier: str = "ANY", device: str = "T7", connection: str = "ANY"):
        try:
            from labjack import ljm  # noqa: WPS433 (lazy, optional dependency)
        except ImportError as exc:  # pragma: no cover - depends on host install
            raise RuntimeError(
                "labjack-ljm is not installed. Install the LJM runtime and "
                "`pip install labjack-ljm`, or run with the mock transport."
            ) from exc
        self._ljm = ljm
        self._handle = ljm.openS(device, connection, identifier)
        self._i2c_ready = False

    # ---- analog ----------------------------------------------------------
    def read_analog(self, names: Sequence[str]) -> List[float]:
        vals = self._ljm.eReadNames(self._handle, len(names), list(names))
        return [float(v) for v in vals]

    def write_register(self, names: Sequence[str], values: Sequence[float]) -> None:
        self._ljm.eWriteNames(self._handle, len(names), list(names),
                              [float(v) for v in values])

    # ---- I²C -------------------------------------------------------------
    def i2c_config(self, sda_dion: int, scl_dion: int) -> None:
        self._ljm.eWriteName(self._handle, "I2C_SDA_DIONUM", float(sda_dion))
        self._ljm.eWriteName(self._handle, "I2C_SCL_DIONUM", float(scl_dion))
        # Default options; throttle 0 -> ~100 kHz. ADS1115 supports up to 400 kHz.
        self._ljm.eWriteName(self._handle, "I2C_OPTIONS", 0.0)
        self._ljm.eWriteName(self._handle, "I2C_SPEED_THROTTLE", 0.0)
        self._i2c_ready = True

    def i2c_xfer(self, address: int, tx: bytes, num_rx: int) -> Tuple[bytes, bool]:
        if not self._i2c_ready:
            raise RuntimeError("i2c_config() must be called before i2c_xfer()")
        ljm, h = self._ljm, self._handle
        ljm.eWriteName(h, "I2C_SLAVE_ADDRESS", float(address))
        ljm.eWriteName(h, "I2C_NUM_BYTES_TX", float(len(tx)))
        ljm.eWriteName(h, "I2C_NUM_BYTES_RX", float(num_rx))
        if tx:
            ljm.eWriteNameByteArray(h, "I2C_DATA_TX", len(tx), list(tx))
        ljm.eWriteName(h, "I2C_GO", 1.0)
        acks = int(ljm.eReadName(h, "I2C_ACKS"))
        rx = b""
        if num_rx:
            data = ljm.eReadNameByteArray(h, "I2C_DATA_RX", num_rx)
            rx = bytes(int(b) & 0xFF for b in data)
        return rx, acks > 0

    def info(self) -> Dict[str, object]:
        name = self._ljm.eReadNameString(self._handle, "DEVICE_NAME_DEFAULT")
        serial = int(self._ljm.eReadName(self._handle, "SERIAL_NUMBER"))
        fw = float(self._ljm.eReadName(self._handle, "FIRMWARE_VERSION"))
        return {"backend": "ljm", "device_name": name, "serial": serial, "firmware": fw}

    def close(self) -> None:
        try:
            self._ljm.close(self._handle)
        except Exception:  # pragma: no cover - best-effort close
            pass


# ==========================================================================
# Mock: physical board + T7 + ADS1115, hardware-free
# ==========================================================================
@dataclass
class ChannelState:
    """Physical truth for one channel that the mock turns into ADC readings."""

    r_rtd_ohms: float
    current_a: float
    r_ref_ohms: float
    excess_noise_v: float = 0.0   # extra white noise on V_RTD (series-chain emulation)
    crd_noise_frac: float = 3e-5  # fractional CRD current noise (seen on V_ref; Stage 8)
    fault: str = ""               # "", "open", "shorted_rtd"


def default_t7_noise_v(config: BoardConfig) -> float:
    """Representative T7 white-noise floor for the configured range.

    ~3 µV rms on ±0.1 V -- order-of-magnitude correct for the high-resolution
    reads the stages request. Tunable per run.
    """
    return config.t7_range_v * 3e-5


def default_ads_noise_v(config: BoardConfig) -> float:
    """Representative ADS1115 input-referred white noise (~2 LSB at ±0.256 V)."""
    lsb = config.ads_range_v / 32768.0
    return max(2.0 * lsb, 5e-6)


def make_scenario(
    config: BoardConfig = DEFAULT_CONFIG,
    temps_c: Optional[Sequence[float]] = None,
    current_spread: float = 0.05,
    r_ref_tol: float = 5e-5,
    seed: int = 0,
) -> Dict[int, ChannelState]:
    """Build a plausible per-channel truth: distinct temps, CRD spread, R_ref tol.

    The ±5 % current spread (the CRD's ±10 % tolerance, half-width) and the R_ref
    tolerance are exactly what cross-cal absorbs into C; noise is identical across
    channels (position-independent) -- the board's design goal.
    """
    rng = np.random.default_rng(seed)
    if temps_c is None:
        lo, hi = config.temp_range_c
        temps_c = list(np.linspace(lo + 0.3 * (hi - lo), hi - 0.3 * (hi - lo), config.n_channels))
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
    """A synthetic *old* board whose V_RTD noise grows up the chain.

    Used to exercise the Stage-5 position-dependence detector and to fabricate a
    baseline dataset. Not representative of the new (per-channel-loop) board.
    """
    states = make_scenario(config, seed=seed)
    for ch, st in states.items():
        st.excess_noise_v = base_noise_v + per_channel_growth_v * ch
    return states


class MockTransport(Transport):
    """Hardware-free transport: simulates the board, T7 analog, and ADS1115 I²C."""

    def __init__(
        self,
        config: BoardConfig = DEFAULT_CONFIG,
        scenario: Optional[Dict[int, ChannelState]] = None,
        seed: int = 12345,
        t7_noise_v: Optional[float] = None,
        ads_noise_v: Optional[float] = None,
    ):
        self.config = config
        self.scenario = scenario if scenario is not None else make_scenario(config)
        self.t7_noise_v = t7_noise_v if t7_noise_v is not None else default_t7_noise_v(config)
        self.ads_noise_v = ads_noise_v if ads_noise_v is not None else default_ads_noise_v(config)
        self._rng = np.random.default_rng(seed)
        self._registers: Dict[str, float] = {}
        self._t7_rev = config.t7_reverse_lookup()
        # ADS1115 device state per present address (power-on config default).
        self._ads_present = set(config.ads_addresses)
        self._ads: Dict[int, Dict[str, int]] = {
            a: {"config": 0x8583, "pointer": ADS_REG_CONVERSION, "conv": 0}
            for a in self._ads_present
        }
        self._sda = config.i2c_sda_dion
        self._scl = config.i2c_scl_dion

    # ---- analog (V_RTD on the T7 diff pairs) -----------------------------
    def _read_vrtd(self, ch: int) -> float:
        st = self.scenario[ch]
        rng_v = self.config.t7_range_v
        if st.fault == "open":
            return rng_v  # railed -> compliance failure
        r_rtd = 0.0 if st.fault == "shorted_rtd" else st.r_rtd_ohms
        base = st.current_a * r_rtd
        sigma = float(np.hypot(self.t7_noise_v, st.excess_noise_v))
        v = base + sigma * self._rng.standard_normal()
        return float(np.clip(v, -rng_v, rng_v))

    def read_analog(self, names: Sequence[str]) -> List[float]:
        out: List[float] = []
        for name in names:
            if name in self._t7_rev:
                out.append(self._read_vrtd(self._t7_rev[name]))
            else:
                out.append(self._registers.get(name, 0.0))
        return out

    def write_register(self, names: Sequence[str], values: Sequence[float]) -> None:
        for n, v in zip(names, values):
            self._registers[n] = float(v)

    # ---- I²C (V_ref on the ADS1115s) -------------------------------------
    def i2c_config(self, sda_dion: int, scl_dion: int) -> None:
        self._sda, self._scl = sda_dion, scl_dion

    def _channel_for(self, address: int, mux: int) -> Optional[int]:
        chip = address - 0x48
        ch = chip * 2 + (1 if mux == ADS_MUX_2_3 else 0)
        return ch if ch in self.scenario else None

    def _ads_raw(self, address: int, mux: int, pga: int) -> int:
        """Signed 16-bit conversion the chip would latch for this (mux, pga)."""
        ch = self._channel_for(address, mux)
        if ch is None:
            return 0
        st = self.scenario[ch]
        i = st.current_a * (1.0 + st.crd_noise_frac * self._rng.standard_normal())
        v = i * st.r_ref_ohms + self.ads_noise_v * self._rng.standard_normal()
        lsb = pga_lsb_volts(pga)
        raw = int(round(v / lsb))
        return int(np.clip(raw, -32768, 32767))

    def i2c_xfer(self, address: int, tx: bytes, num_rx: int) -> Tuple[bytes, bool]:
        if address not in self._ads_present:
            return b"\x00" * num_rx, False  # NACK: nobody home
        st = self._ads[address]
        if tx:
            st["pointer"] = tx[0]
            if tx[0] == ADS_REG_CONFIG and len(tx) >= 3:
                cfg = (tx[1] << 8) | tx[2]
                if cfg & 0x8000:  # OS write = 1 -> start single conversion
                    mux = (cfg >> 12) & 0x7
                    pga = (cfg >> 9) & 0x7
                    st["conv"] = self._ads_raw(address, mux, pga)
                # store config but report OS=1 (idle/conversion-ready) on read-back
                st["config"] = cfg | 0x8000
        rx = b""
        if num_rx:
            val = st["config"] if st["pointer"] == ADS_REG_CONFIG else (st["conv"] & 0xFFFF)
            full = bytes([(val >> 8) & 0xFF, val & 0xFF])
            rx = (full + b"\x00" * num_rx)[:num_rx]
        return rx, True

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
