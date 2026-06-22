"""Board / measurement configuration for the REF200 RTD readout board.

Single source of truth for the bench tooling's electrical parameters and the
T7 AIN channel map. Everything here traces back to ``docs/board_spec.md``; the
defaults reproduce the **resolved configuration** (Pt100, 3 channels, 100 uA,
R_ref = 100 ohm, full-differential 4-wire, +/-0.1 V AIN). The whole module is
parameterized so switching to Pt1000 (or a different channel count / mode) is a
one-call change, not a rewrite -- see ``make_config()`` and ``preset()``.

Spec references:
  - measurement equation, unit cell ....... board_spec.md sec.1
  - current & R_ref selection ............. board_spec.md sec.3
  - AIN modes & channel-count limits ...... board_spec.md sec.5
  - resolved configuration ................ board_spec.md "Resolved configuration"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# T7 register code that selects single-ended (negative terminal = internal GND).
T7_GND_NEG_CH = 199

# Measurement modes (board_spec.md sec.5). Each sets AIN-per-channel and max channels.
MODE_FULL_DIFF = "full_differential"        # 4 AIN/ch, max 3 ch, best noise
MODE_SE_SUBTRACT = "single_ended_subtract"  # 3 SE/ch, max 4 ch
MODE_CAL_CURRENT = "calibrated_current"     # 2 AIN/ch, max 7 ch, drops V_ref

# Quantity keys used throughout the tooling.
Q_VREF = "vref"        # voltage across R_ref           (full-diff / SE)
Q_VRTD = "vrtd"        # voltage across the RTD (Kelvin) (all modes)
Q_TOP = "top"          # top-of-R_ref node vs GND        (SE subtract)
Q_SENSEP = "sensep"    # RTD sense+ node vs GND          (SE subtract)
Q_SENSEN = "sensen"    # RTD sense- node vs GND          (SE subtract)

# IEC 60751 Callendar-Van Dusen coefficients (shared by Pt100 and Pt1000).
CVD_A = 3.9083e-3
CVD_B = -5.775e-7
CVD_C = -4.183e-12  # only used below 0 degC


@dataclass(frozen=True)
class AINPin:
    """One physical T7 analog read: a positive AIN, optional negative AIN.

    ``neg is None``  -> single-ended (negative terminal = GND, code 199).
    ``neg = pos+1``  -> differential pair (T7 even/odd pairing).
    """

    quantity: str
    pos: int
    neg: Optional[int] = None

    @property
    def read_name(self) -> str:
        return f"AIN{self.pos}"

    @property
    def negative_ch(self) -> int:
        return self.neg if self.neg is not None else T7_GND_NEG_CH

    @property
    def differential(self) -> bool:
        return self.neg is not None


@dataclass(frozen=True)
class BoardConfig:
    """Complete electrical + acquisition configuration for one bench run."""

    rtd_type: str                 # "Pt100" | "Pt1000"
    r0_ohms: float                # RTD nominal at 0 degC
    n_channels: int
    excitation_current_a: float   # per-channel source current
    r_ref_ohms: float             # precision reference resistor (nominal)
    measurement_mode: str
    ain_range_v: float            # T7 AIN +/- range
    resolution_index: int         # T7 RESOLUTION_INDEX (0 = device default)
    settling_us: float            # T7 AIN settling time (0 = auto); guards mux-settling risk
    temp_range_c: Tuple[float, float] = (-50.0, 150.0)
    r_ref_tolerance: float = 1e-4       # 0.01 %
    r_ref_tempco_ppm_per_c: float = 10  # <=10 ppm/degC
    # Per-channel AIN assignment: channel -> {quantity -> AINPin}
    ain_map: Dict[int, Dict[str, AINPin]] = field(default_factory=dict)

    # ---- derived expected values (spec sec.3) ----------------------------
    @property
    def v_ref_nominal(self) -> float:
        return self.excitation_current_a * self.r_ref_ohms

    def v_rtd_nominal(self, r_rtd: float) -> float:
        return self.excitation_current_a * r_rtd

    @property
    def channels(self) -> List[int]:
        return list(range(self.n_channels))

    # ---- AIN helpers -----------------------------------------------------
    def pins_for_channel(self, ch: int) -> Dict[str, AINPin]:
        return self.ain_map[ch]

    def all_pins(self) -> List[Tuple[int, AINPin]]:
        out: List[Tuple[int, AINPin]] = []
        for ch in self.channels:
            for pin in self.ain_map[ch].values():
                out.append((ch, pin))
        return out

    def read_names(self) -> List[str]:
        """Flat list of AIN read registers for a full scan (scan order)."""
        return [pin.read_name for _ch, pin in self.all_pins()]

    def reverse_lookup(self) -> Dict[str, Tuple[int, str]]:
        """Map a read register name back to (channel, quantity)."""
        rev: Dict[str, Tuple[int, str]] = {}
        for ch, pin in self.all_pins():
            rev[pin.read_name] = (ch, pin.quantity)
        return rev

    def summary(self) -> str:
        return (
            f"{self.rtd_type} R0={self.r0_ohms:g}ohm  "
            f"{self.n_channels}ch  I={self.excitation_current_a * 1e6:g}uA  "
            f"R_ref={self.r_ref_ohms:g}ohm  mode={self.measurement_mode}  "
            f"range=+/-{self.ain_range_v:g}V  res_idx={self.resolution_index}  "
            f"settling={self.settling_us:g}us"
        )


# --------------------------------------------------------------------------
# AIN map builders (one per mode; spec sec.5)
# --------------------------------------------------------------------------
def _map_full_diff(n: int) -> Dict[int, Dict[str, AINPin]]:
    """4 AIN/ch: V_ref diff pair + V_RTD diff pair. Max 3 ch (12 of 14 AIN)."""
    if n > 3:
        raise ValueError("full_differential supports at most 3 channels (4 AIN each)")
    m: Dict[int, Dict[str, AINPin]] = {}
    for ch in range(n):
        base = ch * 4
        m[ch] = {
            Q_VREF: AINPin(Q_VREF, base, base + 1),
            Q_VRTD: AINPin(Q_VRTD, base + 2, base + 3),
        }
    return m


def _map_se_subtract(n: int) -> Dict[int, Dict[str, AINPin]]:
    """3 SE/ch: TOP, Sense+, Sense- each vs GND. Max 4 ch (12 AIN)."""
    if n > 4:
        raise ValueError("single_ended_subtract supports at most 4 channels (3 AIN each)")
    m: Dict[int, Dict[str, AINPin]] = {}
    for ch in range(n):
        base = ch * 3
        m[ch] = {
            Q_TOP: AINPin(Q_TOP, base, None),
            Q_SENSEP: AINPin(Q_SENSEP, base + 1, None),
            Q_SENSEN: AINPin(Q_SENSEN, base + 2, None),
        }
    return m


def _map_cal_current(n: int) -> Dict[int, Dict[str, AINPin]]:
    """2 AIN/ch: V_RTD diff pair only (V_ref dropped). Max 7 ch (14 AIN)."""
    if n > 7:
        raise ValueError("calibrated_current supports at most 7 channels (2 AIN each)")
    m: Dict[int, Dict[str, AINPin]] = {}
    for ch in range(n):
        base = ch * 2
        m[ch] = {Q_VRTD: AINPin(Q_VRTD, base, base + 1)}
    return m


_MAP_BUILDERS = {
    MODE_FULL_DIFF: _map_full_diff,
    MODE_SE_SUBTRACT: _map_se_subtract,
    MODE_CAL_CURRENT: _map_cal_current,
}


def build_ain_map(mode: str, n_channels: int) -> Dict[int, Dict[str, AINPin]]:
    try:
        return _MAP_BUILDERS[mode](n_channels)
    except KeyError:
        raise ValueError(f"unknown measurement_mode {mode!r}") from None


# --------------------------------------------------------------------------
# Config factory
# --------------------------------------------------------------------------
def make_config(
    rtd_type: str = "Pt100",
    n_channels: int = 3,
    excitation_current_a: Optional[float] = None,
    r_ref_ohms: Optional[float] = None,
    measurement_mode: str = MODE_FULL_DIFF,
    ain_range_v: Optional[float] = None,
    resolution_index: int = 8,
    settling_us: float = 0.0,
) -> BoardConfig:
    """Build a BoardConfig, filling spec-derived defaults for the RTD type.

    Defaults follow the resolved configuration for Pt100 (100 uA, R_ref 100 ohm,
    +/-0.1 V). Pt1000 defaults follow board_spec.md sec.3 (100 uA, R_ref 1 kohm,
    +/-1 V). Any field can be overridden by the caller.
    """
    rtd_type = rtd_type.strip()
    if rtd_type.lower() in ("pt100", "pt-100", "100"):
        rtd_type = "Pt100"
        r0 = 100.0
        cur = excitation_current_a if excitation_current_a is not None else 100e-6
        rref = r_ref_ohms if r_ref_ohms is not None else 100.0
        rng = ain_range_v if ain_range_v is not None else 0.1
    elif rtd_type.lower() in ("pt1000", "pt-1000", "1000"):
        rtd_type = "Pt1000"
        r0 = 1000.0
        cur = excitation_current_a if excitation_current_a is not None else 100e-6
        rref = r_ref_ohms if r_ref_ohms is not None else 1000.0
        rng = ain_range_v if ain_range_v is not None else 1.0
    else:
        raise ValueError(f"unsupported rtd_type {rtd_type!r} (use 'Pt100' or 'Pt1000')")

    return BoardConfig(
        rtd_type=rtd_type,
        r0_ohms=r0,
        n_channels=n_channels,
        excitation_current_a=cur,
        r_ref_ohms=rref,
        measurement_mode=measurement_mode,
        ain_range_v=rng,
        resolution_index=resolution_index,
        settling_us=settling_us,
        ain_map=build_ain_map(measurement_mode, n_channels),
    )


# Named presets for the two RTD types (resolved config = PT100_DEFAULT).
def preset(name: str) -> BoardConfig:
    name = name.lower()
    if name in ("pt100", "default", "resolved"):
        return make_config(rtd_type="Pt100", n_channels=3)
    if name == "pt1000":
        return make_config(rtd_type="Pt1000", n_channels=3)
    if name == "pt1000_cal":  # density example: 7-ch calibrated-current
        return make_config(
            rtd_type="Pt1000", n_channels=7, measurement_mode=MODE_CAL_CURRENT
        )
    raise ValueError(f"unknown preset {name!r}")


# The active default the stage scripts import when no override is given.
DEFAULT_CONFIG = preset("default")