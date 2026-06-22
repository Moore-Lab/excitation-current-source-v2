"""host — reusable acquisition library for the dual-ADC RTD readout board.

This is the *real* measurement code (DIRECTORY_MANAGEMENT.md "host/ vs test/"),
not test scaffolding: the T7 LJM driver for V_RTD, the ADS1115 I²C driver for
V_ref, the time-aligned dual-ADC read, and the ratiometric + cross-calibration
math. The staged bench procedures in ``test/`` import this package; the same
code takes the real measurements on the bench.

Architecture (board_spec.md "The measurement"):

    R_RTD = C · (V_RTD / V_ref)          measured live, ratiometric across 2 ADCs
    C     = R_known · (V_ref / V_RTD)|_known     one-time cross-calibration

V_RTD is read by the T7 on its existing differential pairs; V_ref is digitized
on-board by ADS1115(s) over I²C carried on the T7's digital lines (one LJM
device drives both). C folds R_ref's value, the T7/ADS gain ratio and fixed
offsets into a single per-channel constant, so only stability (not absolute
value) of R_ref and the converters matters.
"""

from __future__ import annotations

__all__ = [
    "config",
    "rtd",
    "transport",
    "t7_rtd",
    "ads1115",
    "acquire",
    "measurement",
    "calibration",
    "paths",
]
