"""Turn measured voltages into resistance and temperature.

Two recovery paths, both 4-wire Kelvin (board_spec.md sec.1 / sec.5):

  ratiometric        R = R_ref * V_RTD / V_ref     (current cancels; the default)
  calibrated-current R = V_RTD / I_cal             (uses Stage-2 calibration constant)

The ratiometric form is the whole point of the board -- the REF200's absolute
value and drift drop out. Calibrated-current is the density fallback when V_ref
is not measured per channel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from config.board_config import BoardConfig, MODE_CAL_CURRENT, Q_VREF, Q_VRTD
from lib.rtd import temp_from_resistance


@dataclass
class ChannelResult:
    channel: int
    v_ref: Optional[float]      # None in calibrated-current mode
    v_rtd: float
    r_calc: float
    t_calc: float
    method: str                 # "ratiometric" | "calibrated_current"
    i_used_a: Optional[float] = None  # current used (calibrated-current mode)


def ratiometric_resistance(v_rtd: float, v_ref: float, r_ref: float) -> float:
    if v_ref == 0.0:
        raise ZeroDivisionError("V_ref is zero -- check R_ref connection / compliance")
    return r_ref * (v_rtd / v_ref)


def calibrated_resistance(v_rtd: float, i_cal_a: float) -> float:
    if i_cal_a == 0.0:
        raise ZeroDivisionError("calibration current is zero")
    return v_rtd / i_cal_a


def compute_channel(
    config: BoardConfig,
    channel: int,
    voltages: Dict[str, float],
    i_cal_a: Optional[float] = None,
) -> ChannelResult:
    """Compute R and T for one channel from its collapsed voltages.

    Uses ratiometric when V_ref is present, else calibrated-current (which
    requires ``i_cal_a`` from the Stage-2 calibration file).
    """
    v_rtd = voltages[Q_VRTD]
    if config.measurement_mode == MODE_CAL_CURRENT or Q_VREF not in voltages:
        if i_cal_a is None:
            raise ValueError(
                f"channel {channel}: calibrated-current mode needs a calibration "
                "constant (run Stage 2 first)"
            )
        r = calibrated_resistance(v_rtd, i_cal_a)
        t = temp_from_resistance(r, config.r0_ohms)
        return ChannelResult(channel, None, v_rtd, r, t, "calibrated_current", i_cal_a)

    v_ref = voltages[Q_VREF]
    r = ratiometric_resistance(v_rtd, v_ref, config.r_ref_ohms)
    t = temp_from_resistance(r, config.r0_ohms)
    return ChannelResult(channel, v_ref, v_rtd, r, t, "ratiometric")


def compute_all(
    config: BoardConfig,
    voltages_by_channel: Dict[int, Dict[str, float]],
    calibration: Optional[Dict[int, float]] = None,
) -> Dict[int, ChannelResult]:
    out: Dict[int, ChannelResult] = {}
    for ch, volts in voltages_by_channel.items():
        i_cal = calibration.get(ch) if calibration else None
        out[ch] = compute_channel(config, ch, volts, i_cal_a=i_cal)
    return out