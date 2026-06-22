"""rtd.py — RTD temperature/resistance physics (Callendar–Van Dusen).

Single source of truth for converting between RTD resistance and temperature, used
by the accuracy analysis to map a resistance error onto an *equivalent temperature
error in degC* (the key Track-B deliverable).

Supports Pt100 and Pt1000 via the standard IEC 60751 coefficients. Pt1000 is the
same curve scaled by R0, so one set of coefficients serves both.

CVD curve:
    R(T) = R0 * (1 + A*T + B*T^2)                      for  0 <= T
    R(T) = R0 * (1 + A*T + B*T^2 + C*(T-100)*T^3)       for  T <  0

Inverse R->T uses the closed form for T>=0 and a bounded numeric solve for T<0.
"""

from __future__ import annotations

# IEC 60751 / DIN EN 60751 coefficients (alpha = 0.00385)
A = 3.9083e-3
B = -5.775e-7
C = -4.183e-12  # only used for T < 0 degC


def r0_for(rtd_type: str) -> float:
    t = rtd_type.strip().lower()
    if t in ("pt100", "pt-100", "100"):
        return 100.0
    if t in ("pt1000", "pt-1000", "1000"):
        return 1000.0
    raise ValueError(f"unknown RTD type {rtd_type!r} (expected Pt100 or Pt1000)")


def r_of_t(temp_c: float, rtd_type: str = "Pt100") -> float:
    """Resistance (ohm) at temperature temp_c (degC)."""
    r0 = r0_for(rtd_type)
    t = float(temp_c)
    if t >= 0.0:
        return r0 * (1.0 + A * t + B * t * t)
    return r0 * (1.0 + A * t + B * t * t + C * (t - 100.0) * t**3)


def dr_dt(temp_c: float, rtd_type: str = "Pt100") -> float:
    """Local sensitivity dR/dT (ohm/degC) at temp_c — used to convert dR -> dT."""
    r0 = r0_for(rtd_type)
    t = float(temp_c)
    if t >= 0.0:
        return r0 * (A + 2.0 * B * t)
    # derivative of the T<0 branch: d/dT[(T-100)*T^3] = 4*T^3 - 300*T^2
    return r0 * (A + 2.0 * B * t + C * (4.0 * t**3 - 300.0 * t**2))


def t_of_r(res_ohm: float, rtd_type: str = "Pt100") -> float:
    """Inverse: temperature (degC) for a given resistance (ohm)."""
    r0 = r0_for(rtd_type)
    ratio = float(res_ohm) / r0
    if ratio >= 1.0:
        # T >= 0 closed form: solve B*T^2 + A*T + (1 - ratio) = 0
        disc = A * A - 4.0 * B * (1.0 - ratio)
        return (-A + disc**0.5) / (2.0 * B)
    # T < 0: bounded bisection on the full quartic branch (monotonic over -200..0)
    lo, hi = -200.0, 0.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if r_of_t(mid, rtd_type) < res_ohm:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


if __name__ == "__main__":
    # quick self-check
    for typ in ("Pt100", "Pt1000"):
        r0 = r0_for(typ)
        print(f"{typ}: R(0)={r_of_t(0,typ):.4f}  R(100)={r_of_t(100,typ):.4f}  "
              f"R(-50)={r_of_t(-50,typ):.4f}  R(150)={r_of_t(150,typ):.4f}")
        print(f"   dR/dT@0 = {dr_dt(0,typ):.5f} ohm/degC ; "
              f"round-trip T(R(25))={t_of_r(r_of_t(25,typ),typ):.4f} degC")
