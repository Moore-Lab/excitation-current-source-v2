"""Board / acquisition configuration for the dual-ADC RTD readout board.

Single source of truth for the electrical parameters and the two converter maps:
the T7 differential pairs that read **V_RTD**, and the ADS1115 chip/input
assignment that reads **V_ref** over I²C. Everything traces back to
``docs/board_spec.md``; the defaults reproduce the resolved design point
(board_spec.md "Resolved inputs", Session 002):

    Pt100, 3 channels, ~220 µA CRD, R_ref ≈ 910 Ω,
    T7 range ±0.1 V, ADS1115 PGA range ±0.256 V,
    2 ADS1115 at 0x48 / 0x49 (1 chip per 2 channels), 3 V_ref reads (1 spare).

The whole module is parameterized: switching to Pt1000 or changing the channel
count (up to 7) is a one-call change (``make_config`` / ``preset``), not a
rewrite. Counts derive from the channel count exactly as the spec describes
(``ceil(n/2)`` ADS1115 chips), so the tooling scales with the board.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# T7 register code selecting single-ended (negative terminal = internal GND).
T7_GND_NEG_CH = 199

# Quantity keys used throughout the acquisition + bench code.
Q_VREF = "vref"   # voltage across R_ref, read by an ADS1115 (I²C)
Q_VRTD = "vrtd"   # voltage across the RTD (Kelvin), read by the T7 diff pair

# ADS1115 differential MUX selections actually wired on this board
# (board_spec.md "Components / ADS1115": AIN0-AIN1 and AIN2-AIN3 per chip).
# These are the raw 3-bit MUX field values; the driver packs them into the
# config register. Kept here because they are a board-wiring fact, not protocol.
ADS_MUX_0_1 = 0b000   # IN+ = AIN0, IN- = AIN1
ADS_MUX_2_3 = 0b011   # IN+ = AIN2, IN- = AIN3

# Selectable ADS1115 I²C addresses via the ADDR strap (board_spec.md).
ADS_ADDRESSES = (0x48, 0x49, 0x4A, 0x4B)
ADS_BASE_ADDRESS = 0x48


@dataclass(frozen=True)
class T7Pin:
    """One T7 differential analog read for a channel's V_RTD (Kelvin sense pair)."""

    channel: int
    pos: int            # positive AIN index
    neg: int            # negative AIN index (even/odd diff pairing)

    @property
    def read_name(self) -> str:
        return f"AIN{self.pos}"


@dataclass(frozen=True)
class ADSInput:
    """One ADS1115 differential read for a channel's V_ref."""

    channel: int
    address: int        # I²C 7-bit address (0x48..0x4B)
    mux: int            # 3-bit MUX field (ADS_MUX_0_1 / ADS_MUX_2_3)

    @property
    def pair_label(self) -> str:
        return "AIN0-1" if self.mux == ADS_MUX_0_1 else "AIN2-3"

    @property
    def addr_hex(self) -> str:
        return f"0x{self.address:02X}"


@dataclass(frozen=True)
class BoardConfig:
    """Complete electrical + acquisition configuration for one bench run."""

    rtd_type: str                  # "Pt100" | "Pt1000"
    r0_ohms: float                 # RTD nominal at 0 degC
    n_channels: int
    excitation_current_a: float    # per-channel CRD current (nominal; measured live)
    r_ref_ohms: float              # reference resistor (nominal; value absorbed into C)
    # --- T7 side (V_RTD) ---
    t7_range_v: float              # T7 AIN ± range
    t7_resolution_index: int       # T7 RESOLUTION_INDEX (0 = device default)
    t7_settling_us: float          # T7 AIN settling time (guards mux settling)
    # --- ADS1115 side (V_ref) ---
    ads_range_v: float             # ADS1115 PGA full-scale (±), e.g. 0.256 V
    ads_data_rate_sps: int         # ADS1115 conversion data rate
    ads_navg: int                  # ADS conversions averaged per V_ref read
    # --- I²C transport pins on the T7 (real backend only) ---
    i2c_sda_dion: int = 0          # FIO/EIO line number for SDA
    i2c_scl_dion: int = 1          # FIO/EIO line number for SCL
    # --- stability metadata (not precision; cross-cal absorbs value) ---
    r_ref_tempco_ppm_per_c: float = 10.0   # <=10 ppm/degC target
    temp_range_c: Tuple[float, float] = (-50.0, 150.0)
    # --- maps (built by the factory) ---
    t7_map: Dict[int, T7Pin] = field(default_factory=dict)
    ads_map: Dict[int, ADSInput] = field(default_factory=dict)

    # ---- derived expected values (board_spec.md "Components") ------------
    @property
    def channels(self) -> List[int]:
        return list(range(self.n_channels))

    @property
    def v_ref_nominal(self) -> float:
        return self.excitation_current_a * self.r_ref_ohms

    def v_rtd_nominal(self, r_rtd: float) -> float:
        return self.excitation_current_a * r_rtd

    @property
    def n_ads_chips(self) -> int:
        """1 ADS1115 per 2 channels (2 differential inputs each)."""
        return math.ceil(self.n_channels / 2)

    @property
    def ads_addresses(self) -> List[int]:
        """Distinct ADS1115 addresses in use, in scan order."""
        seen: List[int] = []
        for ch in self.channels:
            a = self.ads_map[ch].address
            if a not in seen:
                seen.append(a)
        return seen

    # ---- read helpers ----------------------------------------------------
    def t7_read_names(self) -> List[str]:
        return [self.t7_map[ch].read_name for ch in self.channels]

    def t7_reverse_lookup(self) -> Dict[str, int]:
        return {self.t7_map[ch].read_name: ch for ch in self.channels}

    def summary(self) -> str:
        return (
            f"{self.rtd_type} R0={self.r0_ohms:g}ohm  {self.n_channels}ch  "
            f"I~{self.excitation_current_a * 1e6:g}uA  R_ref~{self.r_ref_ohms:g}ohm  "
            f"T7=±{self.t7_range_v:g}V/res{self.t7_resolution_index}/set{self.t7_settling_us:g}us  "
            f"ADS=±{self.ads_range_v:g}V/{self.ads_data_rate_sps}SPS/navg{self.ads_navg}  "
            f"{self.n_ads_chips}chip@{','.join(f'0x{a:02X}' for a in self.ads_addresses)}"
        )


# --------------------------------------------------------------------------
# Map builders
# --------------------------------------------------------------------------
def build_t7_map(n_channels: int) -> Dict[int, T7Pin]:
    """Channel ch -> T7 differential pair (AIN{2ch} / AIN{2ch+1}).

    The T7 Pro has 7 differential pairs; up to 7 RTD channels map onto them
    one-to-one (board_spec.md: the 7 pairs are committed to V_RTD).
    """
    if not 1 <= n_channels <= 7:
        raise ValueError("n_channels must be 1..7 (T7 has 7 differential pairs)")
    return {ch: T7Pin(ch, pos=2 * ch, neg=2 * ch + 1) for ch in range(n_channels)}


def build_ads_map(n_channels: int) -> Dict[int, ADSInput]:
    """Channel ch -> ADS1115 (address, MUX): 1 chip per 2 channels.

    ch even -> chip's AIN0-1, ch odd -> AIN2-3; chip index = ch // 2 ->
    address 0x48 + index. 3 channels -> 0x48 (ch0,ch1) + 0x49 (ch2), matching
    the resolved configuration (board_spec.md "Resolved inputs").
    """
    if not 1 <= n_channels <= 7:
        raise ValueError("n_channels must be 1..7")
    if math.ceil(n_channels / 2) > len(ADS_ADDRESSES):
        raise ValueError("more ADS1115 chips required than available addresses")
    m: Dict[int, ADSInput] = {}
    for ch in range(n_channels):
        chip = ch // 2
        mux = ADS_MUX_0_1 if ch % 2 == 0 else ADS_MUX_2_3
        m[ch] = ADSInput(ch, address=ADS_BASE_ADDRESS + chip, mux=mux)
    return m


# --------------------------------------------------------------------------
# Config factory
# --------------------------------------------------------------------------
def make_config(
    rtd_type: str = "Pt100",
    n_channels: int = 3,
    excitation_current_a: float = None,
    r_ref_ohms: float = None,
    t7_range_v: float = None,
    t7_resolution_index: int = 12,
    t7_settling_us: float = 0.0,
    ads_range_v: float = 0.256,
    ads_data_rate_sps: int = 128,
    ads_navg: int = 16,
) -> BoardConfig:
    """Build a BoardConfig, filling spec-derived defaults for the RTD type.

    Pt100 defaults follow the resolved configuration (≈220 µA, R_ref ≈910 Ω,
    T7 ±0.1 V). Pt1000 follows board_spec.md (T7 ±1 V; R_ref keys off the ADS
    range, not the RTD, so it is unchanged). Any field may be overridden.
    """
    key = rtd_type.strip().lower().replace("-", "")
    if key in ("pt100", "100"):
        rtd_type, r0 = "Pt100", 100.0
        rng = t7_range_v if t7_range_v is not None else 0.1
    elif key in ("pt1000", "1000"):
        rtd_type, r0 = "Pt1000", 1000.0
        rng = t7_range_v if t7_range_v is not None else 1.0
    else:
        raise ValueError(f"unsupported rtd_type {rtd_type!r} (use 'Pt100' or 'Pt1000')")

    # CRD current and R_ref are spec defaults; both are absorbed by cross-cal,
    # so these set ranges/sanity, not precision (board_spec.md "The measurement").
    cur = excitation_current_a if excitation_current_a is not None else 220e-6
    # R_ref sized to the ADS range, not the RTD: V_ref ≈ 0.78 * full-scale at
    # nominal current, with headroom for the CRD's +10 % spread.
    rref = r_ref_ohms if r_ref_ohms is not None else 910.0

    return BoardConfig(
        rtd_type=rtd_type,
        r0_ohms=r0,
        n_channels=n_channels,
        excitation_current_a=cur,
        r_ref_ohms=rref,
        t7_range_v=rng,
        t7_resolution_index=t7_resolution_index,
        t7_settling_us=t7_settling_us,
        ads_range_v=ads_range_v,
        ads_data_rate_sps=ads_data_rate_sps,
        ads_navg=ads_navg,
        t7_map=build_t7_map(n_channels),
        ads_map=build_ads_map(n_channels),
    )


def preset(name: str) -> BoardConfig:
    name = name.lower()
    if name in ("pt100", "default", "resolved"):
        return make_config(rtd_type="Pt100", n_channels=3)
    if name == "pt1000":
        return make_config(rtd_type="Pt1000", n_channels=3)
    if name == "pt100_7ch":  # scalability example: fully populated board
        return make_config(rtd_type="Pt100", n_channels=7)
    raise ValueError(f"unknown preset {name!r}")


# The active default the tooling imports when no override is given.
DEFAULT_CONFIG = preset("default")