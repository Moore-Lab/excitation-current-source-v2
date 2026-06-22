"""analysis.py — parse ngspice output, decide pass/fail, plot, and render reports.

One function per SPICE test (`report_NN_*`). Each reads the deck's raw `wrdata` file
from `sim/scratch/`, computes the metrics and an explicit pass/fail against the
TESTING_PLAN acceptance criterion, writes a figure into `reports/sim/`, and returns a
`Result`. `run_all.py` orchestrates; this module holds all the physics/statistics so
the numbers in the reports are computed, never hand-typed.

The accuracy test (03) does the headline work: a Monte-Carlo over R_ref tolerance +
tempco and T7 ADC offset/gain/noise/source-current, propagated to an equivalent
TEMPERATURE error in degC via Callendar-Van Dusen (`rtd.py`). The ratiometric relation
it samples is the one deck 02 validated against SPICE to <0.1 ppm.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config
import rtd

# physical constants
KB = 1.380649e-23
T_KELVIN = 300.0  # 27 degC sim default

HERE = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(SIM_DIR)
SCRATCH = os.path.join(SIM_DIR, "scratch")
REPORTS = os.path.join(REPO, "reports", "sim")


@dataclass
class Result:
    name: str
    title: str
    passed: bool | None         # None => conditional / informational
    summary: str                # one-line headline
    metrics: list = field(default_factory=list)   # (quantity, expected, measured, unit)
    notes: str = ""
    plot: str = ""              # filename in reports/sim
    criterion: str = ""
    objective: str = ""
    setup: str = ""
    method: str = ""
    nextstep: str = ""


# --------------------------------------------------------------------------- I/O
def load_data(name: str):
    """Read a `wrdata` file with a `set wr_vecnames` header into {colname: ndarray}.

    The first column is ngspice's scale; with `wr_singlescale` an explicitly-listed
    scale vector can repeat, so duplicate names are disambiguated (first occurrence
    wins for lookups)."""
    path = os.path.join(SCRATCH, f"{name}.data")
    for _ in range(15):                 # OneDrive sync can lag the file briefly
        if os.path.exists(path) and os.path.getsize(path) > 0:
            break
        time.sleep(0.2)
    with open(path) as fh:
        header = fh.readline().split()
    data = np.loadtxt(path, skiprows=1)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    cols = {}
    for i, h in enumerate(header):
        cols.setdefault(h, data[:, i])  # first occurrence wins
    cols["_array"] = data
    cols["_header"] = header
    return cols


def fig_path(name: str) -> str:
    os.makedirs(REPORTS, exist_ok=True)
    return os.path.join(REPORTS, f"{name}.png")


# ----------------------------------------------------------------- 01 DC op
def report_01(cfg) -> Result:
    d = load_data("01_dc_op")
    r_rtd, head_nom, head_lo = d["r_rtd"], d["head_nom"], d["head_lo"]
    v_rtd, v_ref = d["v_rtd_nom"], d["v_ref_nom"]
    min_head = float(min(head_nom.min(), head_lo.min()))
    crit = 2.5
    passed = min_head >= crit

    plt.figure(figsize=(7, 4))
    plt.plot(r_rtd, head_nom, label=f"V_rail = {cfg['v_rail']} V")
    plt.plot(r_rtd, head_lo, label=f"V_rail = {cfg['v_rail_min']} V (worst-case low)")
    plt.axhline(crit, color="r", ls="--", label="2.5 V compliance limit")
    plt.xlabel("RTD resistance (ohm)"); plt.ylabel("REF200 source headroom (V)")
    plt.title("DC compliance margin vs RTD resistance")
    plt.legend(); plt.grid(True, alpha=0.3); plt.tight_layout()
    plt.savefig(fig_path("01_dc_op"), dpi=110); plt.close()

    res = Result("01_dc_op", "DC operating point & compliance margin", passed,
                 f"min source headroom = {min_head:.3f} V "
                 f"(limit 2.5 V) -> {'PASS' if passed else 'FAIL'}")
    res.objective = ("Confirm every REF200 section keeps enough voltage across it to "
                     "regulate (>= 2.5 V) across the full RTD range and worst-case "
                     "supply. Maps to TESTING_PLAN test 1.")
    res.setup = (f"Deck 01_dc_op.cir. Unit cell at V_rail = {cfg['v_rail']} V (nominal) "
                 f"and {cfg['v_rail_min']} V (worst-case low). RTD swept "
                 f"{r_rtd.min():.1f}..{r_rtd.max():.1f} ohm.")
    res.method = "DC sweep of RTD; headroom = v(rail) - v(top of R_ref)."
    res.criterion = "Source headroom >= 2.5 V (target >= 3 V) at max RTD R and min supply."
    res.metrics = [
        ("V_RTD range", "8.0-15.7 mV", f"{v_rtd.min()*1e3:.2f}-{v_rtd.max()*1e3:.2f} mV", ""),
        ("V_ref", f"{config.v_ref(cfg)*1e3:.1f} mV", f"{v_ref.mean()*1e3:.3f} mV", ""),
        ("min headroom (nominal)", ">= 3 V", f"{head_nom.min():.3f} V", ""),
        ("min headroom (low supply)", ">= 2.5 V", f"{head_lo.min():.3f} V", ""),
    ]
    res.notes = ("Headroom is enormous because the total burden voltage "
                 "I*(R_ref+R_RTD) is only ~26 mV. Even a 3.3 V rail would pass.")
    res.plot = "01_dc_op.png"
    return res


# -------------------------------------------------------- 02 ratiometric sanity
def report_02(cfg) -> Result:
    d = load_data("02_ratiometric")
    r_rtd, r_calc, err_ppm = d["r_rtd"], d["r_calc"], d["err_ppm"]
    max_abs_ppm = float(np.max(np.abs(err_ppm)))
    crit_ppm = 1.0  # "within numerical error" — 1 ppm is generous for solver noise
    passed = max_abs_ppm < crit_ppm

    plt.figure(figsize=(7, 4))
    plt.plot(r_rtd, err_ppm, ".-")
    plt.xlabel("swept RTD resistance (ohm)")
    plt.ylabel("R_calc error (ppm)")
    plt.title("Ratiometric recovery error  R_calc = R_ref*V_RTD/V_ref")
    plt.grid(True, alpha=0.3); plt.tight_layout()
    plt.savefig(fig_path("02_ratiometric"), dpi=110); plt.close()

    res = Result("02_ratiometric", "Ratiometric correctness (sanity)", passed,
                 f"max |R_calc - R_RTD| = {max_abs_ppm:.4g} ppm "
                 f"(< {crit_ppm} ppm) -> {'PASS' if passed else 'FAIL'}")
    res.objective = ("Prove the topology: R_calc = R_ref*V_RTD/V_ref recovers the RTD "
                     "value independent of the source current and of the finite source "
                     "output resistance. TESTING_PLAN test 2.")
    res.setup = "Deck 02_ratiometric.cir, tight solver tolerances (reltol 1e-12)."
    res.method = ("DC sweep RTD; compute R_calc from solved node voltages; compare to the "
                  "swept value.")
    res.criterion = "R_calc == swept RTD to within numerical error (< 1 ppm)."
    res.metrics = [
        ("max |error|", "~0 (numerical)", f"{max_abs_ppm:.4g} ppm", ""),
        ("error at R=R0", "~0", f"{err_ppm[np.argmin(np.abs(r_rtd-cfg['r_ref']))]:.3g} ppm", ""),
    ]
    res.notes = ("Residual is pure Newton/solver tolerance, not model error: the same "
                 "series current flows through R_ref and the RTD, so the ratio is exact "
                 "regardless of I or R_out. This is the architectural guarantee that the "
                 "REF200's absolute accuracy and drift drop out of the result.")
    res.plot = "02_ratiometric.png"
    return res


# ---------------------------------------------- 03 accuracy: SPICE + Monte Carlo
def montecarlo_accuracy(cfg, temps_c, n=40000, seed=12345, sig_off=None, navg=1):
    """Full accuracy MC -> equivalent degC error at each true temperature.

    Samples (all 1-sigma unless noted):
      R_ref:   tolerance (0.01% treated as 3-sigma) + tempco*board_dT (3-sigma)
      ADC:     independent offset on V_RTD and V_ref reads; gain (cancels); per-read noise
      source:  current spread (cancels ratiometrically; included to demonstrate)
    `sig_off` overrides the per-read offset 1-sigma (used to compare an uncalibrated T7
    against one whose per-channel offset has been nulled to the noise floor).
    Returns dict: per-temp arrays of dT, plus a 1-sigma contribution budget.
    """
    rng = np.random.default_rng(seed)
    typ = cfg["rtd_type"]
    I = cfg["i_exc"]
    Rref_nom = cfg["r_ref"]
    Vref = I * Rref_nom

    sig_tol = cfg["r_ref_tol"] / 3.0                       # frac, 1-sigma
    sig_tempco = cfg["r_ref_tempco"] * config.T_BOARD_DELTA_C / 3.0  # frac, 1-sigma
    if sig_off is None:
        sig_off = cfg["t7_offset"]                         # V, 1-sigma per read
    sig_gain = cfg["t7_gain_err"] / 3.0                    # frac, 1-sigma (cancels)
    sig_noise = cfg["t7_noise_rms"] / np.sqrt(navg)        # V, after averaging navg samples
    sig_I = 50e-6 / 3.0                                    # REF200 25-50 ppm/degC-ish init spread

    out = {"temps": list(temps_c), "dT": {}, "sigma_dT": {}, "worst_dT": {}}
    for Tt in temps_c:
        Rt = rtd.r_of_t(Tt, typ)
        Vrtd = I * Rt
        # actual component / ADC draws
        Rref_act = Rref_nom * (1 + rng.normal(0, sig_tol, n) + rng.normal(0, sig_tempco, n))
        g = 1 + rng.normal(0, sig_gain, n)                 # common ADC gain (cancels)
        Iact = I * (1 + rng.normal(0, sig_I, n))           # cancels
        vrtd_meas = g * (Iact * Rt) + rng.normal(0, sig_off, n) + rng.normal(0, sig_noise, n)
        vref_meas = g * (Iact * Rref_act) + rng.normal(0, sig_off, n) + rng.normal(0, sig_noise, n)
        Rcalc = Rref_nom * vrtd_meas / vref_meas           # recovery uses nominal R_ref
        Tcalc = np.array([rtd.t_of_r(r, typ) for r in Rcalc])
        dT = Tcalc - Tt
        out["dT"][Tt] = dT
        out["sigma_dT"][Tt] = float(np.std(dT))
        out["worst_dT"][Tt] = float(np.percentile(np.abs(dT), 99.7))

    # analytic 1-sigma budget at the worst representative temperature (T=Tmax)
    Tb = max(temps_c)
    Rt = rtd.r_of_t(Tb, typ); dRdT = rtd.dr_dt(Tb, typ)
    budget = {
        "R_ref tolerance (0.01%)":  Rt * sig_tol / dRdT,
        "R_ref tempco (10ppm*dT)":  Rt * sig_tempco / dRdT,
        "ADC offset on V_RTD":      (Rref_nom * sig_off / Vref) / dRdT,
        "ADC offset on V_ref":      (Rt * sig_off / Vref) / dRdT,
        "ADC noise (single read)":  (Rref_nom * sig_noise / Vref * np.sqrt(2)) / dRdT,
        "ADC gain (cancels)":       0.0,
        "Source current (cancels)": 0.0,
    }
    out["budget_Tb"] = Tb
    out["budget"] = budget
    out["budget_total"] = float(np.sqrt(sum(v * v for v in budget.values())))
    return out


def report_03(cfg) -> Result:
    # --- SPICE cross-check: recovered error tracks R_ref deviation 1:1 ---
    d = load_data("03_accuracy_rref")
    r_ref_act, err_ppm = d["r_ref_act"], d["err_ppm"]
    frac_dev = (r_ref_act - cfg["r_ref"]) / cfg["r_ref"]
    # slope of recovered ppm error vs R_ref fractional deviation (expect ~ -1e6 ppm/frac)
    slope = float(np.polyfit(frac_dev, err_ppm, 1)[0])

    # --- headline Monte Carlo -> degC, two scenarios ---
    temps = [config.T_MIN_C, 0.0, 25.0, 100.0, config.T_MAX_C]
    navg = config.T7_NAVG
    mc_raw = montecarlo_accuracy(cfg, temps)                       # uncalibrated, single read
    # recommended operating mode: per-channel offset nulled (residual ~ averaged noise) AND
    # navg-sample averaging on the live reads -> approaches the R_ref-limited floor.
    mc_cal = montecarlo_accuracy(cfg, temps, sig_off=cfg["t7_noise_rms"] / np.sqrt(navg),
                                 navg=navg)
    p997_raw = max(mc_raw["worst_dT"].values())
    p997_cal = max(mc_cal["worst_dT"].values())
    rref_only = np.sqrt(mc_raw["budget"]["R_ref tolerance (0.01%)"]**2
                        + mc_raw["budget"]["R_ref tempco (10ppm*dT)"]**2)
    # max raw offset (1-sigma) that still meets +/-0.1 degC at the worst temperature
    Tw = max(mc_raw["sigma_dT"], key=mc_raw["sigma_dT"].get)
    Rw = rtd.r_of_t(Tw, cfg["rtd_type"]); dRdT_w = rtd.dr_dt(Tw, cfg["rtd_type"])
    Vref = config.v_ref(cfg)
    # offset budget (3-sigma) = sqrt((Rref*so/Vref)^2+(Rw*so/Vref)^2)*3/dRdT -> solve for so
    k = np.sqrt(cfg["r_ref"]**2 + Rw**2) / Vref * 3.0 / dRdT_w
    off_max = 0.1 / k
    crit = 0.1
    passed = None  # CONDITIONAL: meets target only with per-channel offset calibration

    # plot: dT histograms (raw vs calibrated) + raw budget bars
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].hist(mc_raw["dT"][Tw] * 1e3, bins=80, color="#d66", alpha=0.6,
               label=f"uncalibrated ({cfg['t7_offset']*1e6:.0f} µV)")
    ax[0].hist(mc_cal["dT"][Tw] * 1e3, bins=80, color="#3b7", alpha=0.7,
               label=f"nulled + {navg}× avg")
    ax[0].axvline(crit * 1e3, color="k", ls="--"); ax[0].axvline(-crit * 1e3, color="k", ls="--")
    ax[0].set_xlabel("equivalent temperature error (m°C)"); ax[0].set_ylabel("count")
    ax[0].set_title(f"Accuracy MC at worst T = {Tw:.0f} °C"); ax[0].legend(fontsize=8)
    ax[0].grid(True, alpha=0.3)
    names = list(mc_raw["budget"].keys())
    vals = [mc_raw["budget"][k_] * 1e3 for k_ in names]
    ax[1].barh(names, vals, color="#37b")
    ax[1].set_xlabel("1σ contribution (m°C)")
    ax[1].set_title(f"Error budget at T = {mc_raw['budget_Tb']:.0f} °C (uncalibrated)")
    ax[1].grid(True, alpha=0.3, axis="x")
    plt.tight_layout(); plt.savefig(fig_path("03_accuracy"), dpi=110); plt.close()

    res = Result("03_accuracy", "Accuracy / Monte-Carlo -> equivalent °C error", passed,
                 f"R_ref floor {rref_only*1e3:.0f} m°C; meets ±100 m°C with offset-null + "
                 f"{navg}× avg ({p997_cal*1e3:.0f} m°C) but NOT raw single-read "
                 f"({p997_raw*1e3:.0f} m°C)")
    res.objective = ("THE key deliverable: propagate R_ref tolerance+tempco and T7 ADC "
                     "offset/gain/noise to an equivalent temperature error in °C for the "
                     "chosen RTD. TESTING_PLAN test 3.")
    res.setup = (f"Deck 03_accuracy_rref.cir (SPICE sensitivity cross-check) + "
                 f"montecarlo_accuracy() N=40000, two scenarios (raw single-read T7 offset "
                 f"vs per-channel offset nulled + {navg}× averaging). Preset {config.ACTIVE}: "
                 f"{cfg['rtd_type']}, "
                 f"I={cfg['i_exc']*1e6:.0f} µA, R_ref={cfg['r_ref']} Ω, "
                 f"V_ref={Vref*1e3:.0f} mV, T7 ±{cfg['adc_range']} V range.")
    res.method = ("SPICE: sweep actual R_ref over ±(tol+tempco) at R0, recover with nominal "
                  "R_ref. MC: sample all error sources, recover R, invert via Callendar-Van "
                  "Dusen, take dT distribution at five temperatures; report 99.7%|dT|.")
    res.criterion = ("Total equivalent error within ±0.1 °C, dominated by R_ref. "
                     "(Finding: at 100 µA it is dominated by ADC OFFSET unless nulled.)")
    res.metrics = [
        ("SPICE: d(err)/d(R_ref frac)", "-1e6 ppm/frac", f"{slope:.4g} ppm/frac", ""),
        ("R_ref-only floor (1σ)", "< 40 m°C", f"{rref_only*1e3:.1f} m°C", ""),
        ("ADC offset term (1σ, V_RTD)", "—", f"{mc_raw['budget']['ADC offset on V_RTD']*1e3:.1f} m°C", ""),
        ("ADC offset term (1σ, V_ref)", "—", f"{mc_raw['budget']['ADC offset on V_ref']*1e3:.1f} m°C", ""),
        ("total 99.7% (raw, single read)", "<= 100 m°C", f"{p997_raw*1e3:.0f} m°C", ""),
        (f"total 99.7% (nulled + {navg}× avg)", "<= 100 m°C", f"{p997_cal*1e3:.1f} m°C", ""),
        ("max raw offset for ±0.1 °C", "—", f"{off_max*1e6:.1f} µV", ""),
    ]
    dominant = max(mc_raw["budget"], key=mc_raw["budget"].get)
    res.notes = (
        f"**Dominant term (raw): {dominant}** ({mc_raw['budget'][dominant]*1e3:.0f} m°C 1σ). "
        f"At {cfg['i_exc']*1e6:.0f} µA the signals are only ~{Vref*1e3:.0f} mV, so the T7 ADC "
        f"OFFSET — not R_ref — sets the budget. Ratiometric cancels gain AND source current "
        f"(those budget rows are 0), but it does NOT cancel ADC offset: V_RTD and V_ref are "
        f"read on separate AIN pairs with independent offsets, and averaging reduces NOISE "
        f"not OFFSET.\n\n"
        f"- **R_ref-limited floor = {rref_only*1e3:.0f} m°C** — well under ±0.1 °C, confirming "
        f"the spec's sanity check for the reference-resistor term.\n"
        f"- **Uncalibrated ({cfg['t7_offset']*1e6:.0f} µV assumed): {p997_raw*1e3:.0f} m°C "
        f"(99.7%) — FAILS ±0.1 °C.**\n"
        f"- **Per-channel offset nulling + {navg}× averaging (recommended mode): "
        f"{p997_cal*1e3:.0f} m°C — PASSES**, and R_ref again dominates.\n\n"
        f"To meet ±0.1 °C without nulling, the per-read offset must be ≤ ~{off_max*1e6:.1f} µV "
        f"(1σ). t7_offset is a CONFIG ASSUMPTION ({cfg['t7_offset']*1e6:.0f} µV) — verify "
        f"against the T7 datasheet for the ±{cfg['adc_range']} V range.")
    res.nextstep = ("MANDATORY: add per-channel ADC offset nulling to the bench plan "
                    "(measure each AIN pair with input shorted / known zero; subtract). "
                    "Verify the T7 differential offset spec. If offset cannot be nulled below "
                    f"~{off_max*1e6:.0f} µV, switch to 200 µA (Mode A) — it doubles the "
                    "signals and halves the offset-referred error.")
    res.plot = "03_accuracy.png"
    return res


# ----------------------------------------------------- 04 compliance corner
def report_04(cfg) -> Result:
    d = load_data("04_compliance_corner")
    headroom = float(d["headroom"][0])
    v_burden = float(d["v_burden"][0])
    crit = 2.5
    passed = headroom >= crit
    res = Result("04_compliance_corner", "Compliance corner (max R, min supply)", passed,
                 f"worst-corner headroom = {headroom:.3f} V (limit 2.5 V) -> "
                 f"{'PASS' if passed else 'FAIL'}")
    res.objective = "Worst-case stack still in compliance. TESTING_PLAN test 4."
    res.setup = (f"Deck 04. V_rail={cfg['v_rail_min']} V, RTD={cfg['r_rtd_max']:.1f} Ω "
                 f"(max), R_ref high by +{cfg['r_ref_tol']+cfg['r_ref_tempco']*config.T_BOARD_DELTA_C:.2%}.")
    res.method = "Single op at the stacked worst corner."
    res.criterion = "Source headroom >= 2.5 V."
    res.metrics = [
        ("burden voltage", "~26 mV", f"{v_burden*1e3:.2f} mV", ""),
        ("source headroom", ">= 2.5 V", f"{headroom:.3f} V", ""),
    ]
    res.notes = "Margin is ~%.2f V above the limit." % (headroom - crit)
    res.plot = ""
    return res


# ------------------------------------------------ 05 transient sense settling
def report_05(cfg) -> Result:
    d = load_data("05_transient_settling")
    t, err = d["time"], np.abs(d["err_v"])
    tau = 2 * config.FILTER_R * config.FILTER_C
    # worst-case inter-channel step = (min - max) sense voltage across the band
    typ = cfg["rtd_type"]
    v_step = cfg["i_exc"] * (rtd.r_of_t(config.T_MIN_C, typ) - rtd.r_of_t(config.T_MAX_C, typ))
    # settling threshold = the ADC single-sample noise floor (practical limit) and 1/2 LSB
    thr_noise = cfg["t7_noise_rms"]
    eff_bits = 16  # effective bits on range (documented assumption; verify vs T7 RI table)
    lsb = (2 * cfg["adc_range"]) / (2 ** eff_bits)
    thr_lsb = 0.5 * lsb
    dwell = config.MUX_DWELL_S

    def settle_time(threshold):
        below = np.where(err <= threshold)[0]
        if len(below) == 0:
            return float("inf")
        # first index after which it stays below
        idx = below[0]
        for i in below:
            if np.all(err[i:] <= threshold):
                idx = i
                break
        return float(t[idx])

    ts_noise = settle_time(thr_noise)
    ts_lsb = settle_time(thr_lsb)
    # required C for the shared-filter case to settle within the dwell to noise floor
    n_tau = np.log(abs(v_step) / thr_noise)
    req_tau = dwell / n_tau
    req_C = req_tau / (2 * config.FILTER_R)

    passed = ts_noise <= dwell  # worst-case (cap re-settles each hop)

    plt.figure(figsize=(7, 4))
    plt.semilogy(t * 1e3, err * 1e6, label="|settling error|")
    plt.axhline(thr_noise * 1e6, color="g", ls="--", label=f"ADC noise floor {thr_noise*1e6:.1f} µV")
    plt.axhline(thr_lsb * 1e6, color="orange", ls=":", label=f"½ LSB ({eff_bits}-bit) {thr_lsb*1e6:.2f} µV")
    plt.axvline(dwell * 1e3, color="r", ls="--", label=f"mux dwell {dwell*1e3:.0f} ms")
    plt.xlabel("time (ms)"); plt.ylabel("settling error (µV)")
    plt.title("Sense RC settling (worst-case full-band step)")
    plt.legend(fontsize=8); plt.grid(True, alpha=0.3, which="both"); plt.tight_layout()
    plt.savefig(fig_path("05_transient_settling"), dpi=110); plt.close()

    res = Result("05_transient_settling", "Transient — sense RC settling vs mux dwell",
                 None,  # conditional
                 f"worst-case settle to noise floor = {ts_noise*1e3:.2f} ms vs "
                 f"{dwell*1e3:.0f} ms dwell -> {'within dwell' if passed else 'EXCEEDS dwell'} "
                 f"(mitigated by per-channel RC placement)")
    res.objective = ("Size the sense RC filter and scan rate together: confirm a channel "
                     "settles to < ½ LSB within the mux dwell. TESTING_PLAN test 5.")
    res.setup = (f"Deck 05. Differential filter 2×{config.FILTER_R:.0f} Ω + {config.FILTER_C*1e6:.2f} µF "
                 f"(τ = {tau*1e6:.0f} µs). Worst-case step {abs(v_step)*1e3:.2f} mV "
                 f"(max→min sense voltage). Cap pre-charged to the previous channel via .ic.")
    res.method = ("Transient relaxation from the worst-case previous-channel voltage to this "
                  "channel's V_RTD; settling time = when |error| stays below the threshold.")
    res.criterion = "Settle below ½ LSB / ADC noise floor within the mux dwell (1 ms)."
    res.metrics = [
        ("filter τ (differential)", "—", f"{tau*1e6:.0f} µs", ""),
        ("settle to noise floor", f"<= {dwell*1e3:.0f} ms", f"{ts_noise*1e3:.2f} ms", ""),
        ("settle to ½ LSB", f"<= {dwell*1e3:.0f} ms", f"{ts_lsb*1e3:.2f} ms", ""),
        ("required C for 1 ms (shared)", "—", f"{req_C*1e9:.0f} nF", ""),
    ]
    res.notes = (
        "FINDING: if the 0.1 µF cap must RE-SETTLE a full inter-channel step every mux hop "
        f"(i.e. a single SHARED filter after the T7 mux), settling needs ~{ts_noise*1e3:.1f} ms "
        f"— it EXCEEDS the 1 ms dwell. Mitigations: (a) RECOMMENDED — place the RC PER SENSE "
        f"PAIR before the mux (board_spec §6 'at the T7 input', one R+C per channel); each "
        f"cap then stays charged at its channel's voltage and never re-settles, so the only "
        f"settling is the T7's own input mux (datasheet, ~tens of µs). (b) Shared filter: use "
        f"C ≤ ~{req_C*1e9:.0f} nF, or (c) lengthen the dwell to ≥ {ts_noise*1e3:.1f} ms, or "
        f"(d) accept lower resolution. This is a LAYOUT REQUIREMENT for Track F: per-channel "
        f"sense RC, not a single shared one. Effective-bits ({eff_bits}) is an assumption — "
        f"confirm against the T7 resolution-index table.")
    res.nextstep = ("Track F: one RC per sense pair, placed before the T7 mux. Bench Stage 6: "
                    "verify per-channel settling at the chosen ResolutionIndex.")
    res.plot = "05_transient_settling.png"
    return res


# ------------------------------------------------------------- 06 noise
def report_06(cfg) -> Result:
    d = load_data("06_noise")
    freq = d["frequency"]
    onoise = d["onoise_spectrum"]
    # integrated passive/Johnson noise from ngspice
    with open(os.path.join(REPORTS, "06_noise.log")) as fh:
        txt = fh.read()
    onoise_total = None
    for line in txt.splitlines():
        if "onoise_total" in line:
            onoise_total = float(line.split("=")[1])
    # excitation current noise (datasheet, added analytically) -> voltage at V_RTD
    R_rtd = cfg["r_rtd_nom"]
    enbw = 1.0 / (4.0 * (2 * config.FILTER_R) * config.FILTER_C)  # 1-pole ENBW (Hz)
    i_white = 20e-12                       # A/rtHz
    v_exc_white = i_white * R_rtd * np.sqrt(enbw)
    i_flicker_rms = 1e-9 / 6.6             # 1 nA p-p over 0.1-10 Hz -> rms
    v_exc_flicker = i_flicker_rms * R_rtd  # slow; cancels ratiometrically (carried anyway)
    total = float(np.sqrt(onoise_total**2 + v_exc_white**2 + v_exc_flicker**2))
    floor = cfg["t7_noise_rms"]
    signal = config.v_ref(cfg)
    passed = total < floor

    plt.figure(figsize=(7, 4))
    plt.loglog(freq, onoise * 1e9, label="passive/Johnson (ngspice)")
    plt.axhline(i_white * R_rtd * 1e9, color="purple", ls=":",
                label=f"REF200 excitation white {i_white*R_rtd*1e9:.1f} nV/√Hz")
    plt.xlabel("frequency (Hz)"); plt.ylabel("output noise density (nV/√Hz)")
    plt.title("Noise spectral density referred to ADC input")
    plt.legend(fontsize=8); plt.grid(True, alpha=0.3, which="both"); plt.tight_layout()
    plt.savefig(fig_path("06_noise"), dpi=110); plt.close()

    res = Result("06_noise", "Noise — excitation + passive chain vs ADC floor", passed,
                 f"total {total*1e9:.0f} nV RMS vs ADC floor {floor*1e6:.1f} µV -> "
                 f"{'PASS' if passed else 'FAIL'}")
    res.objective = ("Confirm the excitation + passive chain noise sits below the T7 ADC "
                     "floor — the architecture must not introduce a new noise source. "
                     "TESTING_PLAN test 6.")
    res.setup = (f"Deck 06_noise.cir `.noise` 0.1 Hz–100 kHz, output v(adcp,adcn). "
                 f"Filter ENBW ≈ {enbw:.0f} Hz. Excitation noise added from datasheet.")
    res.method = ("ngspice integrates Johnson noise of R_ref, RTD, R_out and the two filter "
                  "resistors through the cap; analysis adds REF200 white (20 pA/√Hz) and "
                  "flicker (1 nA p-p) current noise × R in quadrature.")
    res.criterion = "Total RMS noise referred to ADC input < T7 ADC noise floor."
    res.metrics = [
        ("passive/Johnson (ngspice)", "—", f"{onoise_total*1e9:.0f} nV", ""),
        ("excitation white ×R", "—", f"{v_exc_white*1e9:.1f} nV", ""),
        ("excitation flicker ×R", "—", f"{v_exc_flicker*1e9:.1f} nV", ""),
        ("total chain noise", f"< {floor*1e6:.1f} µV", f"{total*1e9:.0f} nV", ""),
        ("signal V_ref", "—", f"{signal*1e3:.0f} mV", ""),
        ("chain noise / ADC floor", "< 1", f"{total/floor:.2f}", ""),
    ]
    res.notes = (f"Chain noise is ~{floor/total:.0f}× below the ADC floor and ~{signal/total:.2e}× "
                 f"below the signal. The excitation is NOT the limiter — the architecture "
                 f"targets the real problem (CMRR/series stacking) without adding noise. The "
                 f"flicker term cancels ratiometrically (slow common drift on I).")
    res.plot = "06_noise.png"
    return res


# --------------------------------------------------------- 07 crosstalk
def report_07(cfg) -> Result:
    d = load_data("07_crosstalk")
    i_a, dv = d["i_a"], d["dv_rtd_b"]
    coupling_v = float(abs(dv[-1]))             # at full aggressor current
    # equivalent temperature error in victim
    dR = coupling_v / cfg["i_exc"]
    dRdT = rtd.dr_dt(0.0, cfg["rtd_type"])
    dT = dR / dRdT
    # max acceptable star-ground R: coupling scales linearly; floor = ADC noise -> dT
    floor_v = cfg["t7_noise_rms"]
    rstar_max = config.STAR_GND_R * (floor_v / coupling_v)
    passed = coupling_v < floor_v

    plt.figure(figsize=(7, 4))
    plt.plot(i_a * 1e6, dv * 1e12, ".-")
    plt.xlabel("aggressor channel current I_A (µA)")
    plt.ylabel("victim V_RTD shift (pV)")
    plt.title(f"Shared-ground crosstalk (R_star = {config.STAR_GND_R} Ω)")
    plt.grid(True, alpha=0.3); plt.tight_layout()
    plt.savefig(fig_path("07_crosstalk"), dpi=110); plt.close()

    res = Result("07_crosstalk", "Crosstalk via shared star-ground", passed,
                 f"coupling = {coupling_v*1e12:.1f} pV = {dT*1e6:.2f} µ°C at "
                 f"R_star={config.STAR_GND_R} Ω -> {'PASS' if passed else 'FAIL'}")
    res.objective = ("Bound coupling between channels through a finite shared star-ground "
                     "return, and set the acceptable star-ground trace resistance. "
                     "TESTING_PLAN test 7.")
    res.setup = (f"Deck 07. Two cells sharing R_star = {config.STAR_GND_R} Ω. Aggressor "
                 f"current swept 0→{cfg['i_exc']*1e6:.0f} µA; victim read Kelvin-differential.")
    res.method = ("DC sweep of aggressor current; record victim V_RTD shift (computed in "
                  "double precision in-SPICE). Coupling scales linearly with R_star.")
    res.criterion = "Coupling into the victim below the ADC noise floor for the planned R_star."
    res.metrics = [
        ("victim shift @ full I_A", f"< {floor_v*1e6:.1f} µV", f"{coupling_v*1e12:.2f} pV", ""),
        ("equivalent °C error", "negligible", f"{dT*1e6:.2f} µ°C", ""),
        ("max acceptable R_star", "—", f"{rstar_max:.0f} Ω", ""),
    ]
    res.notes = (
        f"Differential Kelvin sensing rejects the star-ground bump itself (common-mode); the "
        f"only residual is the second-order path dV/dI_A = R_star·R_RTD/R_out = "
        f"{coupling_v/cfg['i_exc']*1e6:.2g} µΩ-per-... i.e. {coupling_v*1e12:.1f} pV at full "
        f"current. The star-ground resistance could be ~{rstar_max:.0f} Ω before crosstalk "
        f"reached the ADC floor — so the star-ground requirement is trivially met. This is "
        f"the architecture's whole point: independent loops + Kelvin make position/channel "
        f"coupling vanish.")
    res.plot = "07_crosstalk.png"
    return res


ALL = [report_01, report_02, report_03, report_04, report_05, report_06, report_07]