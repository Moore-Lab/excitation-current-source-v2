"""RTD resistance <-> temperature conversion (IEC 60751 Callendar-Van Dusen).

Works for Pt100 and Pt1000 by scaling with R0; the CVD coefficients are
identical for both. Used by every stage that turns a measured resistance into a
temperature (and vice-versa, to generate substitution targets and mock data).

  T >= 0 degC:  R(T) = R0 * (1 + A*T + B*T^2)
  T <  0 degC:  R(T) = R0 * (1 + A*T + B*T^2 + C*(T - 100)*T^3)

The forward equation (R from T) is exact. The inverse (T from R) is closed-form
above 0 degC and Newton-iterated below 0 degC, where the cubic term matters.
"""

from __future__ import annotations

from config.board_config import CVD_A, CVD_B, CVD_C


def resistance_from_temp(temp_c: float, r0_ohms: float) -> float:
    """RTD resistance (ohm) at a given temperature (degC)."""
    t = temp_c
    if t >= 0.0:
        ratio = 1.0 + CVD_A * t + CVD_B * t * t
    else:
        ratio = 1.0 + CVD_A * t + CVD_B * t * t + CVD_C * (t - 100.0) * t ** 3
    return r0_ohms * ratio


def temp_from_resistance(r_ohms: float, r0_ohms: float) -> float:
    """Temperature (degC) from RTD resistance (ohm).

    Closed form for T >= 0; Newton refinement (seeded from the linear-ish
    closed-form root) for T < 0 to include the C*(T-100)*T^3 term.
    """
    # Closed-form positive-branch root of R0*(1 + A*T + B*T^2) = R.
    disc = CVD_A * CVD_A - 4.0 * CVD_B * (1.0 - r_ohms / r0_ohms)
    if disc < 0.0:
        raise ValueError(f"resistance {r_ohms} ohm out of representable range for R0={r0_ohms}")
    t_pos = (-CVD_A + disc ** 0.5) / (2.0 * CVD_B)
    if r_ohms >= r0_ohms:  # T >= 0 region; closed form is exact
        return t_pos

    # Below 0 degC: Newton-Raphson on the full quartic, seeded at t_pos.
    t = t_pos
    for _ in range(100):
        f = resistance_from_temp(t, r0_ohms) - r_ohms
        # d/dT of R0*(1 + A T + B T^2 + C (T-100) T^3)
        dfdt = r0_ohms * (
            CVD_A
            + 2.0 * CVD_B * t
            + CVD_C * (4.0 * t ** 3 - 300.0 * t * t)
        )
        if dfdt == 0.0:
            break
        step = f / dfdt
        t -= step
        if abs(step) < 1e-9:
            break
    return t


def temp_error_from_resistance_error(
    r_ohms: float, dr_ohms: float, r0_ohms: float
) -> float:
    """Equivalent temperature error (degC) for a resistance error dr at r.

    Local sensitivity dT/dR via central difference -- used to express accuracy
    budgets and noise in temperature units (TESTING_PLAN Part 2 reporting).
    """
    t_hi = temp_from_resistance(r_ohms + dr_ohms, r0_ohms)
    t_lo = temp_from_resistance(r_ohms - dr_ohms, r0_ohms)
    return 0.5 * (t_hi - t_lo)


def sensitivity_ohms_per_c(temp_c: float, r0_ohms: float) -> float:
    """dR/dT (ohm/degC) at a temperature -- ~0.385 ohm/K for Pt100 near 0 degC."""
    h = 0.01
    return (
        resistance_from_temp(temp_c + h, r0_ohms)
        - resistance_from_temp(temp_c - h, r0_ohms)
    ) / (2.0 * h)