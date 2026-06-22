"""Ratiometric + cross-calibration math (board_spec.md "The measurement").

Because V_RTD and V_ref are measured on *different* ADCs, the raw ratio carries
the converters' gain ratio. A single per-channel constant C folds that gain
ratio, R_ref's value, and fixed offsets together:

    R_RTD = C · (V_RTD / V_ref)                    live measurement
    C     = R_known · (V_ref / V_RTD)|_known        one-time cross-calibration

So the CRD current cancels (same I through R_ref and the RTD), R_ref's absolute
value is absorbed into C, and only stability -- R_ref tempco and the relative
ADC gain tempco between recals -- limits accuracy. C is mandatory: without it a
raw ratio is not a resistance, so ``compute_channel`` requires the constant.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from host.config import BoardConfig, Q_VREF, Q_VRTD
from host.rtd import temp_from_resistance


@dataclass
class ChannelResult:
    channel: int
    v_ref: float
    v_rtd: float
    ratio: float        # V_RTD / V_ref (the raw, converter-gain-bearing ratio)
    c_const: float      # per-channel cross-cal constant used
    r_calc: float       # recovered RTD resistance (ohm)
    t_calc: float       # recovered temperature (degC)


def ratiometric_resistance(v_rtd: float, v_ref: float, c_const: float) -> float:
    """R = C · (V_RTD / V_ref)."""
    if v_ref == 0.0:
        raise ZeroDivisionError("V_ref is zero -- check ADS1115 / R_ref connection")
    return c_const * (v_rtd / v_ref)


def cross_cal_constant(r_known: float, v_rtd: float, v_ref: float) -> float:
    """C = R_known · (V_ref / V_RTD), measured with a known resistor in place of the RTD."""
    if v_rtd == 0.0:
        raise ZeroDivisionError("V_RTD is zero -- check the T7 sense pair / R_known")
    return r_known * (v_ref / v_rtd)


def compute_channel(
    config: BoardConfig,
    channel: int,
    voltages: Dict[str, float],
    c_const: Optional[float],
) -> ChannelResult:
    """Recover R and T for one channel from its {V_RTD, V_ref} and constant C."""
    if c_const is None:
        raise ValueError(
            f"channel {channel}: cross-calibration constant C is required "
            "(run Stage 2 cross-calibration first)"
        )
    v_rtd = voltages[Q_VRTD]
    v_ref = voltages[Q_VREF]
    ratio = v_rtd / v_ref if v_ref else float("nan")
    r = ratiometric_resistance(v_rtd, v_ref, c_const)
    t = temp_from_resistance(r, config.r0_ohms)
    return ChannelResult(channel, v_ref, v_rtd, ratio, c_const, r, t)


def compute_all(
    config: BoardConfig,
    voltages_by_channel: Dict[int, Dict[str, float]],
    constants: Dict[int, float],
) -> Dict[int, ChannelResult]:
    out: Dict[int, ChannelResult] = {}
    for ch, volts in voltages_by_channel.items():
        out[ch] = compute_channel(config, ch, volts, constants.get(ch))
    return out
