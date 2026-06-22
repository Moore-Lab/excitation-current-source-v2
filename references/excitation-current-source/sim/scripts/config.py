"""config.py — single design-point definition for the SPICE harness.

Everything downstream (the generated ngspice params include, every deck, every
report) reads its numbers from here, so the whole harness re-targets by editing one
dict. The brief requires the harness be parameterized by RTD type and R_ref so it
serves whatever Lucas picks; `PRESETS` holds both candidate points and `ACTIVE`
selects the resolved one.

Resolved configuration (board_spec.md "Resolved configuration", SESSION_LOG 001):
    Pt100, 3 channels, 100 uA, Mode B, R_ref = 100 ohm, full-diff +/-0.1 V AIN.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Design presets. Each is self-contained so a deck never has to branch on type.
# ---------------------------------------------------------------------------
PRESETS = {
    # The RESOLVED design point for this board.
    "pt100_100u": {
        "rtd_type": "Pt100",
        "i_exc": 100e-6,        # A   excitation current per channel
        "r_ref": 100.0,         # ohm reference resistor (R_ref = R0)
        "r_ref_tol": 1e-4,      # 0.01 % tolerance (fractional, 1-sigma assumed below)
        "r_ref_tempco": 10e-6,  # 10 ppm/degC
        "v_rail": 5.0,          # V   LDO rail
        "rout_src": 50e6,       # ohm REF200 finite output resistance (datasheet 20-100M)
        "adc_range": 0.1,       # V   T7 +/-0.1 V range
        "t7_offset": 8e-6,      # V   ADC offset (per reading, +/-, ~tens of uV worst case)
        "t7_gain_err": 1e-4,    # 0.01 % ADC gain error (cancels in ratio; carried to show it)
        "t7_noise_rms": 1.4e-6, # V   per-sample ADC noise, +/-0.1 V, high res index (datasheet-ish)
    },
    # Pt100 at 200 uA (board_spec section 3 recommendation): Mode A = both REF200 sources
    # paralleled -> 1 channel/chip, current 200 uA, output resistance halves to ~25 MOhm.
    # Doubles the signals (V_ref 20 mV, V_RTD 16-31 mV) and so halves the ADC-offset-referred
    # error that dominated the 100 uA accuracy budget (test 03).
    "pt100_200u": {
        "rtd_type": "Pt100",
        "i_exc": 200e-6,        # A   Mode A: two 100 uA sections in parallel
        "r_ref": 100.0,         # ohm R_ref = R0
        "r_ref_tol": 1e-4,
        "r_ref_tempco": 10e-6,
        "v_rail": 5.0,
        "rout_src": 25e6,       # ohm two 50 MOhm sources in parallel
        "adc_range": 0.1,       # V   +/-0.1 V (V_RTD max 31 mV < 0.1 V)
        "t7_offset": 8e-6,      # same T7 / same range as the 100 uA preset
        "t7_gain_err": 1e-4,
        "t7_noise_rms": 1.4e-6,
    },
    # Alternate point the harness must also serve (Pt1000 / 100 uA / Mode B).
    "pt1000_100u": {
        "rtd_type": "Pt1000",
        "i_exc": 100e-6,
        "r_ref": 1000.0,
        "r_ref_tol": 1e-4,
        "r_ref_tempco": 10e-6,
        "v_rail": 5.0,
        "rout_src": 50e6,
        "adc_range": 1.0,       # +/-1 V range for the larger signal
        "t7_offset": 30e-6,
        "t7_gain_err": 1e-4,
        "t7_noise_rms": 12e-6,
    },
}

ACTIVE = "pt100_200u"   # adopted 2026-06-22 (was pt100_100u); see docs/sessions/trackB.md B-002


# ---------------------------------------------------------------------------
# Operating range & filter / mux constants (shared, not preset-specific)
# ---------------------------------------------------------------------------
T_MIN_C = -50.0     # board_spec operating range
T_MAX_C = 150.0
T_BOARD_DELTA_C = 10.0   # assumed board temperature swing for R_ref tempco budget

# Sense anti-alias / EMI RC filter (board_spec section 6): R in each leg, C across pair.
FILTER_R = 1000.0       # ohm series in EACH sense leg
FILTER_C = 0.1e-6       # F across the differential pair

# T7 scan timing the transient deck checks settling against.
MUX_DWELL_S = 1.0e-3    # planned per-channel dwell (settling budget)

# Software averaging per RTD reading (reduces ADC noise and averaged-null offset by 1/sqrt).
T7_NAVG = 256           # samples averaged per channel reading (recommended operating mode)

# Star-ground shared return resistance for the crosstalk deck.
STAR_GND_R = 0.05       # ohm shared trace resistance (target to validate)


def active() -> dict:
    """The active preset plus derived fields used by the analysis/decks."""
    import rtd
    cfg = dict(PRESETS[ACTIVE])
    cfg["v_rail_min"] = cfg["v_rail"] * 0.95          # worst-case low supply (LDO -5%)
    cfg["r_rtd_min"] = rtd.r_of_t(T_MIN_C, cfg["rtd_type"])
    cfg["r_rtd_max"] = rtd.r_of_t(T_MAX_C, cfg["rtd_type"])
    cfg["r_rtd_nom"] = cfg["r_ref"]                    # R_ref = R0 by design
    cfg["v_ref"] = cfg["i_exc"] * cfg["r_ref"]
    return cfg


def v_ref(cfg: dict) -> float:
    return cfg["i_exc"] * cfg["r_ref"]


if __name__ == "__main__":
    import rtd
    cfg = active()
    print(f"ACTIVE preset: {ACTIVE}")
    for k, v in cfg.items():
        print(f"  {k:14s} = {v}")
    print(f"  V_ref          = {v_ref(cfg)*1e3:.3f} mV")
    rmin = rtd.r_of_t(T_MIN_C, cfg["rtd_type"])
    rmax = rtd.r_of_t(T_MAX_C, cfg["rtd_type"])
    print(f"  R_RTD range    = {rmin:.2f} .. {rmax:.2f} ohm "
          f"({rmin*cfg['i_exc']*1e3:.2f} .. {rmax*cfg['i_exc']*1e3:.2f} mV)")
