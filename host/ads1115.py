"""ADS1115 driver: reads V_ref differentially over I²C.

The current-sense voltage V_ref (across R_ref) is digitized on-board by ADS1115
ADC(s) on the T7's I²C lines (board_spec.md "Current-sense ADC"). This driver
speaks the ADS1115 register protocol over the abstract ``Transport.i2c_xfer``:

  * config register  (0x01): start a single-shot conversion with a chosen MUX,
    PGA and data rate; OS bit starts it / reports completion.
  * conversion reg.  (0x00): the signed 16-bit result; volts = raw * PGA_LSB.

Each channel's V_ref is one differential pair on one chip (config ``ads_map``);
``read_vref`` averages ``n_avg`` conversions to beat the LSB noise on the small
(~200 mV) signal. ``scan`` probes the four selectable addresses for bring-up.
The default PGA range is ±0.256 V (7.8125 µV/LSB), sized so V_ref sits ~78 % of
full-scale at nominal current with headroom for the CRD's +10 % spread.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from host.config import ADS_ADDRESSES, BoardConfig
from host.transport import (
    ADS_PGA_FS_VOLTS,
    ADS_REG_CONFIG,
    ADS_REG_CONVERSION,
    Transport,
    pga_lsb_volts,
)

# Config-register fields (datasheet). MUX is supplied per channel from config.
_OS_SINGLE = 0x8000          # write 1: start single conversion; read 1: idle/ready
_MODE_SINGLE_SHOT = 0x0100   # MODE bit (8)
_COMP_DISABLE = 0x0003       # COMP_QUE = 11 -> comparator disabled

# Data-rate (DR) field [7:5] -> samples/s.
_DR_FIELD = {8: 0b000, 16: 0b001, 32: 0b010, 64: 0b011,
             128: 0b100, 250: 0b101, 475: 0b110, 860: 0b111}


def pga_field_for_range(range_v: float) -> int:
    """ADS1115 PGA field for a ±full-scale voltage (must be a supported range)."""
    for field, fs in ADS_PGA_FS_VOLTS.items():
        if field <= 0b101 and abs(fs - range_v) < 1e-9:
            return field
    raise ValueError(
        f"ADS1115 range ±{range_v} V is not a hardware range "
        f"(choose one of {sorted({v for k, v in ADS_PGA_FS_VOLTS.items() if k <= 0b101})})"
    )


def dr_field_for(sps: int) -> int:
    try:
        return _DR_FIELD[sps]
    except KeyError:
        raise ValueError(f"ADS1115 data rate {sps} SPS unsupported "
                         f"(choose one of {sorted(_DR_FIELD)})") from None


class ADS1115Array:
    """The set of ADS1115 chips reading V_ref for every channel."""

    def __init__(self, transport: Transport, config: BoardConfig, poll_max: int = 64):
        self.transport = transport
        self.config = config
        self.poll_max = poll_max
        self._pga = pga_field_for_range(config.ads_range_v)
        self._dr = dr_field_for(config.ads_data_rate_sps)
        self._lsb = pga_lsb_volts(self._pga)

    # ---- setup -----------------------------------------------------------
    def configure(self) -> None:
        """Point the transport's I²C engine at the board's SDA/SCL lines."""
        self.transport.i2c_config(self.config.i2c_sda_dion, self.config.i2c_scl_dion)

    def scan(self) -> List[int]:
        """Probe the four selectable addresses; return those that acknowledge.

        Stage 1 uses this to confirm every expected ADS1115 is present before
        trusting any V_ref read.
        """
        present: List[int] = []
        for addr in ADS_ADDRESSES:
            _rx, ack = self.transport.i2c_xfer(addr, bytes([ADS_REG_CONFIG]), 2)
            if ack:
                present.append(addr)
        return present

    # ---- reads -----------------------------------------------------------
    def _read_once(self, address: int, mux: int) -> float:
        """One single-shot differential conversion -> volts."""
        cfg = (_OS_SINGLE | (mux << 12) | (self._pga << 9)
               | _MODE_SINGLE_SHOT | (self._dr << 5) | _COMP_DISABLE)
        tx, ack = self.transport.i2c_xfer(
            address, bytes([ADS_REG_CONFIG, (cfg >> 8) & 0xFF, cfg & 0xFF]), 0
        )
        if not ack:
            raise IOError(f"ADS1115 0x{address:02X} did not ACK config write "
                          "(check I²C wiring / address strap)")
        # Poll the OS bit until the conversion is ready; never read stale data
        # from a stuck/NACKing chip.
        for _ in range(self.poll_max):
            rx, _ack = self.transport.i2c_xfer(address, bytes([ADS_REG_CONFIG]), 2)
            if rx and (((rx[0] << 8) | rx[1]) & _OS_SINGLE):
                break
        else:
            raise IOError(f"ADS1115 0x{address:02X} conversion timeout "
                          f"(OS never set in {self.poll_max} polls)")
        rx, _ack = self.transport.i2c_xfer(address, bytes([ADS_REG_CONVERSION]), 2)
        raw = int.from_bytes(rx[:2], byteorder="big", signed=True)
        return raw * self._lsb

    def read_vref(self, ch: int, n_avg: Optional[int] = None) -> float:
        """V_ref for one channel (volts), averaged over ``n_avg`` conversions."""
        n = self.config.ads_navg if n_avg is None else n_avg
        inp = self.config.ads_map[ch]
        acc = 0.0
        for _ in range(max(1, n)):
            acc += self._read_once(inp.address, inp.mux)
        return acc / max(1, n)

    def read_vref_all(self, n_avg: Optional[int] = None) -> Dict[int, float]:
        return {ch: self.read_vref(ch, n_avg=n_avg) for ch in self.config.channels}

    @property
    def lsb_volts(self) -> float:
        return self._lsb