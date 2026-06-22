#!/usr/bin/env python
"""
run_all.py - single headless entry point for the Track B SPICE harness.

  python sim/scripts/run_all.py            # run every deck + analysis + reports
  python sim/scripts/run_all.py --no-run   # re-analyse existing data only

For each TESTING_PLAN Part-1 test it: runs the ngspice deck, loads the wrdata,
computes the pass/fail criterion, writes a plot into reports/sim/plots/ and a
markdown report into reports/sim/, and prints a summary table. Exit code is
non-zero if any test FAILs (a SPICE failure blocks fabrication).

Bench-measurable assumptions (T7/ADS noise, mux dwell, targets) are named
constants below so Lucas can drop in real datasheet/bench numbers later.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spice_io as io

# ===========================================================================
# Bench-measurable assumptions (replace with datasheet/bench numbers as known)
# ===========================================================================
T7_NOISE_RMS_V  = 1.0e-6    # T7 Pro effective RMS noise on +/-0.1 V range  [V]
ADS_NOISE_RMS_V = 5.0e-6    # ADS1115 effective RMS noise (averaged)         [V]
MEAS_BW_HZ      = 10.0      # effective per-channel measurement bandwidth    [Hz]
MUX_DWELL_S     = 5.0e-3    # assumed per-channel mux dwell                  [s]
SETTLE_HALF_LSB_V = 1.0e-6  # 1/2-LSB-equivalent settle target at T7 input   [V]
RES_TARGET_C    = 0.02      # per-channel noise/resolution target            [degC]
VL_CRD          = 1.05      # CRD limiting voltage (regulation floor)        [V]
STAR_GND_BUDGET_OHM = 0.1   # achievable star-ground resistance on the board [Ohm]


def read_param(deck: str, name: str, default: float | None = None) -> float:
    """Pull a `.param NAME = value` (SI suffixes) out of a deck file."""
    txt = (io.NETLIST_DIR / deck).read_text()
    m = re.search(rf"^\.param\s+{name}\s*=\s*([0-9eE.+\-]+)([a-zA-Z]*)",
                  txt, re.MULTILINE)
    if not m:
        if default is not None:
            return default
        raise KeyError(f"{name} not found in {deck}")
    suff = {"u": 1e-6, "m": 1e-3, "k": 1e3, "meg": 1e6, "n": 1e-9, "p": 1e-12}
    return float(m.group(1)) * suff.get(m.group(2).lower(), 1.0)


# ===========================================================================
# Per-test analyses.  Each returns (passed: bool, summary: str).
# ===========================================================================
def t1_dc_compliance():
    nom = io.load_wrdata(io.DATA_DIR / "test1_rail_nom.dat")
    mn  = io.load_wrdata(io.DATA_DIR / "test1_rail_min.dat")
    # cols: rrtd, Vcrd, Vref, Vrtd, Vrail
    rrtd, vcrd_nom = nom[:, 0], nom[:, 1]
    vcrd_min = mn[:, 1]
    worst = float(vcrd_min.min())
    passed = worst > VL_CRD
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(rrtd, vcrd_nom, label="rail 5.0 V")
    ax.plot(rrtd, vcrd_min, label="rail 4.5 V (worst)")
    ax.axhline(VL_CRD, color="r", ls="--", label=f"V_L = {VL_CRD} V")
    ax.set(xlabel="RTD [Ohm]", ylabel="V across CRD [V]",
           title="Test 1 - CRD compliance")
    ax.legend(); ax.grid(True, alpha=.3)
    fig.tight_layout(); fig.savefig(io.PLOT_DIR / "test1_compliance.png", dpi=110)
    plt.close(fig)
    results = (f"| quantity | expected | measured | unit |\n"
               f"|---|---|---|---|\n"
               f"| min V across CRD (rail 4.5 V) | > {VL_CRD} | {worst:.3f} | V |\n"
               f"| margin above V_L | > 0 | {worst - VL_CRD:.3f} | V |\n"
               f"| V_RTD span (Pt100) | 18-35 | "
               f"{1e3*nom[:,3].min():.1f}-{1e3*nom[:,3].max():.1f} | mV |")
    io.write_report(
        "test1_dc_compliance", "Test 1 - DC operating point & CRD compliance",
        {"Objective": "Acceptance (a): the CRD keeps regulating (V across it > V_L) "
                      "across the full Pt100 sweep at the worst-case low rail.",
         "Setup": "Deck sim/netlists/test1_dc_compliance.cir; ngspice op sweep of "
                  "Vrrtd 80-158 Ohm at rail = 5.0 V and 4.5 V; CRD = 220 uA || 5 MOhm.",
         "Method": "Vcrd = v(rail)-v(top) over the sweep; take the minimum at the "
                   "low rail and compare to V_L.",
         "Results": results + "\n\n![compliance](plots/test1_compliance.png)",
         "Pass / Fail": f"Criterion min Vcrd > V_L={VL_CRD} V. "
                        f"**{'PASS' if passed else 'FAIL'}** "
                        f"(margin {worst - VL_CRD:.2f} V).",
         "Next": "Re-point at the exported KiCad netlist in Wave 3."})
    return passed, f"min Vcrd={worst:.2f} V (>{VL_CRD}), margin {worst-VL_CRD:.2f} V"


def t2_ratio_xcal():
    files = {"nom": "test2_nom.dat", "crd_hi": "test2_crd_hi.dat",
             "crd_lo": "test2_crd_lo.dat", "ref_hi": "test2_ref_hi.dat",
             "ref_lo": "test2_ref_lo.dat"}
    d = {k: io.load_wrdata(io.DATA_DIR / v) for k, v in files.items()}
    rrtd = d["nom"][:, 0]
    ratio = {k: v[:, 1] / v[:, 2] for k, v in d.items()}      # V_RTD/V_ref
    cal_i = int(np.argmin(np.abs(rrtd - 100.0)))              # R_known = 100 Ohm
    # nominal cross-cal constant
    C_nom = 100.0 / ratio["nom"][cal_i]
    # (1) CRD perturbations with the NOMINAL C -> live cancellation, no recal
    err_crd = []
    for k in ("nom", "crd_hi", "crd_lo"):
        rcalc = C_nom * ratio[k]
        err_crd.append(np.max(np.abs(rcalc - rrtd) / rrtd))
    err_crd = float(max(err_crd))
    # (2) R_ref perturbations need their own cross-cal -> value absorbed by C
    err_ref = []
    for k in ("ref_hi", "ref_lo"):
        C_k = 100.0 / ratio[k][cal_i]
        rcalc = C_k * ratio[k]
        err_ref.append(np.max(np.abs(rcalc - rrtd) / rrtd))
    err_ref = float(max(err_ref))
    tol = 1e-6
    passed = err_crd < tol and err_ref < tol
    fig, ax = plt.subplots(1, 2, figsize=(9, 4))
    for k in ("nom", "crd_hi", "crd_lo"):
        ax[0].plot(rrtd, C_nom * ratio[k], label=k)
    ax[0].plot(rrtd, rrtd, "k:", label="truth")
    ax[0].set(title="CRD +/-10% with nominal C", xlabel="RTD [Ohm]",
              ylabel="R_calc [Ohm]"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
    for k in ("nom", "ref_hi", "ref_lo"):
        C_k = 100.0 / ratio[k][cal_i]
        ax[1].plot(rrtd, 1e6 * (C_k * ratio[k] - rrtd) / rrtd, label=k)
    ax[1].set(title="R_ref +/-10% residual (own cross-cal)", xlabel="RTD [Ohm]",
              ylabel="R_calc error [ppm]"); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)
    fig.tight_layout(); fig.savefig(io.PLOT_DIR / "test2_xcal.png", dpi=110)
    plt.close(fig)
    results = (f"| case | applied C | max |R_calc-RTD|/RTD |\n|---|---|---|\n"
               f"| CRD +/-10% | nominal (no recal) | {err_crd:.2e} |\n"
               f"| R_ref +/-10% | per-corner recal | {err_ref:.2e} |")
    io.write_report(
        "test2_ratio_xcal", "Test 2 - Ratiometric + cross-cal correctness",
        {"Objective": "Acceptance (b): R_calc = C*V_RTD/V_ref recovers the swept RTD "
                      "and is invariant to +/-10% CRD and R_ref perturbation.",
         "Setup": "Deck test2_ratio_xcal.cir; Vrrtd 80-158 Ohm at five (kc,kref) corners.",
         "Method": "CRD spread checked with the NOMINAL C (proves live current "
                   "cancellation); R_ref spread checked with each corner's own "
                   "cross-cal (proves the value is absorbed into C).",
         "Results": results + "\n\n![xcal](plots/test2_xcal.png)",
         "Pass / Fail": f"Criterion max error < {tol:.0e}. "
                        f"**{'PASS' if passed else 'FAIL'}** "
                        f"(CRD {err_crd:.1e}, R_ref {err_ref:.1e} -> numerical floor).",
         "Next": "Bench Stage 2/3 repeats this with real parts."})
    return passed, f"CRD err {err_crd:.1e}, R_ref err {err_ref:.1e} (tol {tol:.0e})"


def t3_montecarlo():
    ef = io.load_wrdata(io.DATA_DIR / "test3_mc.dat")[:, 1]    # fractional error
    errC = ef * io.PT100_SENS_C
    sigma_C = float(np.std(errC))
    p95 = float(np.percentile(np.abs(errC), 95))
    # analytic per-term breakdown using the deck's own sigmas
    dt = read_param("test3_montecarlo.cir", "DT_HOT")
    s_tcref = read_param("test3_montecarlo.cir", "SIG_TCREF")
    s_tcgr = read_param("test3_montecarlo.cir", "SIG_TCGR")
    s_off = read_param("test3_montecarlo.cir", "SIG_OFF")
    v_rtd = 221.0e-6 * 100.0    # V_RTD at RTD_0: I~221 uA x 100 Ohm ~ 22.1 mV
    term_tcref = s_tcref * 1e-6 * dt * io.PT100_SENS_C
    term_tcgr = s_tcgr * 1e-6 * dt * io.PT100_SENS_C
    term_off = (s_off / v_rtd) * io.PT100_SENS_C
    rss = float(np.sqrt(term_tcref**2 + term_tcgr**2 + term_off**2))
    tempco_dominates = min(term_tcref, term_tcgr) >= term_off
    passed = (sigma_C <= 0.05) and tempco_dominates
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(errC, bins=60, color="#4477aa", alpha=.8)
    ax.axvline(sigma_C, color="r", ls="--", label=f"+1sigma={sigma_C:.4f} C")
    ax.axvline(-sigma_C, color="r", ls="--")
    ax.set(xlabel="equivalent Pt100 error [degC]", ylabel="count",
           title=f"Test 3 - MC accuracy (N={len(errC)})")
    ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(io.PLOT_DIR / "test3_mc_hist.png", dpi=110)
    plt.close(fig)
    results = (f"| term | 1-sigma input | degC (1-sigma) |\n|---|---|---|\n"
               f"| R_ref tempco | {s_tcref:g} ppm/C | {term_tcref:.4f} |\n"
               f"| relative ADC gain tempco | {s_tcgr:g} ppm/C | {term_tcgr:.4f} |\n"
               f"| V_RTD offset drift | {s_off*1e6:g} uV | {term_off:.4f} |\n"
               f"| **analytic RSS** | | **{rss:.4f}** |\n"
               f"| **MC sigma (sim)** | | **{sigma_C:.4f}** |\n"
               f"| MC 95th pct \\|err\\| | | {p95:.4f} |")
    io.write_report(
        "test3_montecarlo", "Test 3 - Monte-Carlo accuracy -> degC error",
        {"Objective": "Acceptance (c): over board dT the accuracy is dominated by "
                      "R_ref tempco + relative ADC gain tempco, within target.",
         "Setup": f"Deck test3_montecarlo.cir; N={len(errC)} Gaussian samples; "
                  f"dT={dt:g} C; sigmas R_ref/gain={s_tcref:g}/{s_tcgr:g} ppm/C, "
                  f"offset={s_off*1e6:g} uV; cross-cal C verified = R_ref0 = 910 Ohm.",
         "Method": "Per sample: cross-cal at dt=0, then op at dt with sampled tempco/"
                   "offset; fractional error -> Pt100 degC via x255.9.",
         "Results": results + "\n\n![hist](plots/test3_mc_hist.png)",
         "Pass / Fail": f"Criterion sigma <= 0.05 C AND tempco terms dominate. "
                        f"**{'PASS' if passed else 'FAIL'}** (sigma={sigma_C:.4f} C; "
                        f"each tempco term {term_tcref:.4f} C > offset {term_off:.4f} C).",
         "Anomalies & notes": "Offset term scales as 1/V_RTD (~22 mV), so it is the "
                              "term most sensitive to the small Pt100 signal - tighten "
                              "T7/ADS offset drift or recal more often if it grows.",
         "Next": "Inject real part tempco/offset specs; bench Stage 7 measures C drift."})
    return passed, (f"sigma={sigma_C:.4f} C, RSS={rss:.4f} C, "
                    f"tempco-dominated={tempco_dominates}")


def t4_rref_sizing():
    d = io.load_wrdata(io.DATA_DIR / "test4_vref_vs_kc.dat")   # kc, Vref
    kc, vref = d[:, 0], d[:, 1]
    i_hi = int(np.argmin(np.abs(kc - 1.10)))                   # +10% CRD
    vref_hi = float(vref[i_hi])
    fs_frac = vref_hi / io.ADS_FS
    ebits = np.log2(vref_hi / io.ADS_LSB)
    passed = fs_frac < 0.90
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(kc, 1e3 * vref, label="V_ref")
    ax.axhline(1e3 * io.ADS_FS, color="r", ls="--", label="ADS FS 256 mV")
    ax.axhline(0.9e3 * io.ADS_FS, color="orange", ls=":", label="90% FS")
    ax.axvspan(0.9, 1.1, alpha=.1, color="g", label="CRD +/-10%")
    ax.set(xlabel="CRD current scale kc", ylabel="V_ref [mV]",
           title="Test 4 - R_ref sizing / no-clip")
    ax.legend(fontsize=8); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(io.PLOT_DIR / "test4_sizing.png", dpi=110)
    plt.close(fig)
    results = (f"| quantity | expected | measured | unit |\n|---|---|---|---|\n"
               f"| V_ref at +10% CRD | < 230 | {1e3*vref_hi:.1f} | mV |\n"
               f"| fraction of ADS FS | < 90 | {1e2*fs_frac:.1f} | % |\n"
               f"| effective bits used | high | {ebits:.1f} | bits |")
    io.write_report(
        "test4_rref_sizing", "Test 4 - R_ref sizing / no-clip vs ADS1115 range",
        {"Objective": "Acceptance: worst-case V_ref stays under the ADS1115 +/-0.256 V "
                      "range with margin and good effective bits.",
         "Setup": "Deck test4_rref_sizing.cir; R_ref=910 Ohm; sweep CRD scale kc 0.85-1.15.",
         "Method": "V_ref = drop across R_ref (RTD-independent); evaluate at kc=1.10 "
                   "(+10% CRD) and compare to 90% of full scale.",
         "Results": results + "\n\n![sizing](plots/test4_sizing.png)",
         "Pass / Fail": f"Criterion V_ref(+10%) < 90% FS. "
                        f"**{'PASS' if passed else 'FAIL'}** ({1e2*fs_frac:.0f}% FS).",
         "Next": "If headroom is wanted, R_ref=1k on the +/-0.512 V range."})
    return passed, f"V_ref(+10%)={1e3*vref_hi:.0f} mV = {1e2*fs_frac:.0f}% FS, {ebits:.1f} bits"


def t5_transient():
    d = io.load_wrdata(io.DATA_DIR / "test5_settle.dat")       # time, Vmid, Vt7p
    t, vt7 = d[:, 0], d[:, 2]
    final = float(vt7[-1])
    step_t = 100e-6
    err = np.abs(vt7 - final)
    after = t >= step_t
    bad = np.where(after & (err > SETTLE_HALF_LSB_V))[0]
    settle_t = float(t[bad[-1]] - step_t) if len(bad) else 0.0
    passed = settle_t < MUX_DWELL_S
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(1e3 * t, 1e3 * vt7, label="v(t7p) filtered")
    ax.axhline(1e3 * (final + SETTLE_HALF_LSB_V), color="r", ls=":", label="final +/- 1/2 LSB")
    ax.axhline(1e3 * (final - SETTLE_HALF_LSB_V), color="r", ls=":")
    ax.set(xlabel="time [ms]", ylabel="V [mV]", title="Test 5 - sense RC settling")
    ax.legend(fontsize=8); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(io.PLOT_DIR / "test5_settle.png", dpi=110)
    plt.close(fig)
    results = (f"| quantity | expected | measured | unit |\n|---|---|---|---|\n"
               f"| RC time constant | ~100 | {1e6*1e3*0.1e-6:.0f} | us |\n"
               f"| settle to 1/2 LSB ({SETTLE_HALF_LSB_V*1e6:g} uV) | < {1e3*MUX_DWELL_S:g} | "
               f"{1e3*settle_t:.2f} | ms |\n"
               f"| mux dwell budget | - | {1e3*MUX_DWELL_S:g} | ms |")
    io.write_report(
        "test5_transient_settle", "Test 5 - Sense-line RC settling vs mux dwell",
        {"Objective": "Acceptance: the 1 kOhm/0.1 uF sense filter settles to < 1/2 T7 "
                      "LSB within the per-channel mux dwell.",
         "Setup": "Deck test5_transient_settle.cir; CRD switched on at t=100 us; "
                  "RF=1 kOhm, CF=0.1 uF; .tran to 1.2 ms.",
         "Method": "Find the last time the filtered node is outside final +/- 1/2 LSB; "
                   "compare that settle time to the mux dwell.",
         "Results": results + "\n\n![settle](plots/test5_settle.png)",
         "Pass / Fail": f"Criterion settle < dwell. "
                        f"**{'PASS' if passed else 'FAIL'}** "
                        f"(settle {1e3*settle_t:.2f} ms < {1e3*MUX_DWELL_S:g} ms).",
         "Next": "Confirm the chosen scan dwell on the T7 in Track C / bench."})
    return passed, f"settle {1e3*settle_t:.2f} ms < dwell {1e3*MUX_DWELL_S:g} ms"


def t6_noise():
    nref = io.load_wrdata(io.DATA_DIR / "test6_nref_noise.dat")   # f, V/rtHz
    nrtd = io.load_wrdata(io.DATA_DIR / "test6_nrtd_noise.dat")
    dens_ref = float(np.median(nref[:, 1]))     # flat (white Johnson)
    dens_rtd = float(np.median(nrtd[:, 1]))
    sb = np.sqrt(MEAS_BW_HZ)
    sig_vref = np.hypot(dens_ref * sb, ADS_NOISE_RMS_V)   # V_ref total
    sig_vrtd = np.hypot(dens_rtd * sb, T7_NOISE_RMS_V)    # V_RTD total
    v_ref, v_rtd = 0.201, 0.0221
    f_johnson_adc = np.hypot(sig_vrtd / v_rtd, sig_vref / v_ref)
    c_johnson_adc = f_johnson_adc * io.PT100_SENS_C
    passed = c_johnson_adc < RES_TARGET_C
    # CRD current-noise BOUND (worst case: non-simultaneous sampling -> no cancel)
    f_target = RES_TARGET_C / io.PT100_SENS_C
    rem = f_target**2 - f_johnson_adc**2
    if rem > 0:
        coef = sb * np.hypot(io.R_REF / v_ref, 100.0 / v_rtd)   # frac per A/rtHz
        in_bound = np.sqrt(rem) / coef
    else:
        in_bound = 0.0
    # contribution bar chart (degC)
    contribs = {
        "Johnson R_ref": (dens_ref * sb / v_ref) * io.PT100_SENS_C,
        "Johnson RTD": (dens_rtd * sb / v_rtd) * io.PT100_SENS_C,
        "ADS1115 V_ref": (ADS_NOISE_RMS_V / v_ref) * io.PT100_SENS_C,
        "T7 V_RTD": (T7_NOISE_RMS_V / v_rtd) * io.PT100_SENS_C,
    }
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(range(len(contribs)), [1e3 * v for v in contribs.values()], color="#66ccee")
    ax.set_xticks(range(len(contribs))); ax.set_xticklabels(contribs.keys(), rotation=20, fontsize=8)
    ax.axhline(1e3 * RES_TARGET_C, color="r", ls="--", label=f"target {RES_TARGET_C} C")
    ax.set(ylabel="ratio noise [mC]", title="Test 6 - noise contributions")
    ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(io.PLOT_DIR / "test6_noise.png", dpi=110)
    plt.close(fig)
    results = (f"| source | contribution [degC RMS] |\n|---|---|\n"
               + "".join(f"| {k} | {v*1e3:.4f} m |\n" for k, v in contribs.items())
               + f"| **total (Johnson+ADC)** | **{c_johnson_adc*1e3:.3f} m** |\n"
               + f"| CRD current-noise bound (worst case) | {in_bound*1e9:.2f} nA/rtHz |")
    io.write_report(
        "test6_noise", "Test 6 - Noise of the ratio",
        {"Objective": "Acceptance (d): ratio noise below the per-channel resolution "
                      "target, with the CRD current-noise risk explicitly bounded.",
         "Setup": f"ngspice .noise -> Johnson PSD (V_ref {dens_ref*1e9:.2f}, "
                  f"V_RTD {dens_rtd*1e9:.2f} nV/rtHz); BW={MEAS_BW_HZ:g} Hz; "
                  f"T7 {T7_NOISE_RMS_V*1e6:g} uV, ADS {ADS_NOISE_RMS_V*1e6:g} uV RMS (assumed).",
         "Method": "RSS-combine each path's noise, divide by its signal (V_ref=201 mV, "
                   "V_RTD=22.1 mV), RSS the two fractions, x255.9 -> degC. CRD noise is "
                   "common to both reads: it CANCELS in the ratio under simultaneous "
                   "sampling; the bound is the i_n that would reach target if it did NOT.",
         "Results": results + "\n\n![noise](plots/test6_noise.png)",
         "Pass / Fail": f"Criterion total < {RES_TARGET_C} C. "
                        f"**{'PASS' if passed else 'FAIL'}** "
                        f"({c_johnson_adc*1e3:.2f} mC). CRD bound {in_bound*1e9:.1f} nA/rtHz "
                        f"worst-case; ~0 if T7/ADS sample simultaneously.",
         "Anomalies & notes": "T7/ADS noise are assumptions - replace with datasheet/"
                              "bench. Johnson is negligible; the ADCs dominate.",
         "Next": "Bench Stage 5 (noise/position) and Stage 8 (CRD noise) confirm."})
    return passed, (f"{c_johnson_adc*1e3:.2f} mC (<{RES_TARGET_C*1e3:.0f} mC); "
                    f"CRD bound {in_bound*1e9:.1f} nA/rtHz")


def t7_crosstalk():
    rgs = [("0p01", 0.01), ("0p1", 0.1), ("1", 1.0), ("10", 10.0)]
    coupling_c = {}
    for tag, rg in rgs:
        d = io.load_wrdata(io.DATA_DIR / f"test7_rg_{tag}.dat")   # rrtdA, ratioB
        ratioB = d[:, 1]
        frac = (ratioB.max() - ratioB.min()) / np.mean(ratioB)
        coupling_c[rg] = frac * io.PT100_SENS_C
    at_budget = coupling_c[min(coupling_c, key=lambda r: abs(r - STAR_GND_BUDGET_OHM))]
    passed = at_budget < RES_TARGET_C
    fig, ax = plt.subplots(figsize=(6, 4))
    rg_v = list(coupling_c.keys()); cc = [coupling_c[r] for r in rg_v]
    ax.loglog(rg_v, np.maximum(cc, 1e-18), "o-")
    ax.axhline(RES_TARGET_C, color="r", ls="--", label=f"target {RES_TARGET_C} C")
    ax.axvline(STAR_GND_BUDGET_OHM, color="g", ls=":", label="star-gnd budget")
    ax.set(xlabel="star-ground R [Ohm]", ylabel="victim coupling [degC]",
           title="Test 7 - shared-ground crosstalk")
    ax.legend(fontsize=8); ax.grid(alpha=.3, which="both")
    fig.tight_layout(); fig.savefig(io.PLOT_DIR / "test7_crosstalk.png", dpi=110)
    plt.close(fig)
    results = ("| star-ground R [Ohm] | victim coupling [degC] |\n|---|---|\n"
               + "".join(f"| {r:g} | {c:.2e} |\n" for r, c in coupling_c.items()))
    io.write_report(
        "test7_crosstalk", "Test 7 - Shared-ground crosstalk",
        {"Objective": "Acceptance: coupling between channels sharing a finite star-"
                      "ground return stays below the noise floor; sets max ground R.",
         "Setup": "Deck test7_crosstalk.cir; two unit cells share RG (sg->gnd); sweep "
                  "aggressor RTD 80-158 Ohm at RG = 0.01/0.1/1/10 Ohm; victim at 100 Ohm.",
         "Method": "Kelvin sensing rejects the common ground bounce; residual coupling "
                   "enters only via the CRD's finite Z. Take the victim ratio swing over "
                   "the aggressor's full range -> degC.",
         "Results": results + "\n\n![crosstalk](plots/test7_crosstalk.png)",
         "Pass / Fail": f"Criterion coupling < {RES_TARGET_C} C at the "
                        f"{STAR_GND_BUDGET_OHM} Ohm budget. "
                        f"**{'PASS' if passed else 'FAIL'}** ({at_budget:.1e} C).",
         "Anomalies & notes": "Coupling is at/near the solver's numerical floor - "
                              "Kelvin + current-source isolation makes it negligible for "
                              "any realistic star-ground resistance.",
         "Next": "Bench Stage 6 perturbs one channel and checks the others."})
    return passed, f"coupling at {STAR_GND_BUDGET_OHM} Ohm = {at_budget:.1e} C"


TESTS = [
    ("test1_dc_compliance.cir", "Test 1 DC/compliance", t1_dc_compliance),
    ("test2_ratio_xcal.cir", "Test 2 ratio+xcal", t2_ratio_xcal),
    ("test3_montecarlo.cir", "Test 3 Monte-Carlo", t3_montecarlo),
    ("test4_rref_sizing.cir", "Test 4 R_ref sizing", t4_rref_sizing),
    ("test5_transient_settle.cir", "Test 5 transient", t5_transient),
    ("test6_noise.cir", "Test 6 noise", t6_noise),
    ("test7_crosstalk.cir", "Test 7 crosstalk", t7_crosstalk),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-run", action="store_true",
                    help="skip ngspice; re-analyse existing data")
    args = ap.parse_args()
    for d in (io.DATA_DIR, io.LOG_DIR, io.PLOT_DIR):
        d.mkdir(parents=True, exist_ok=True)
    ng = None
    if not args.no_run:
        ng = io.find_ngspice()
        print(f"ngspice: {ng}\n")
        # appendwrite deck (test3) must start from a clean file
        (io.DATA_DIR / "test3_mc.dat").unlink(missing_ok=True)
        for deck, _, _ in TESTS:
            print(f"  running {deck} ...")
            io.run_deck(deck, ng)
    print("\n=== SUMMARY ===")
    rows, all_pass = [], True
    for deck, name, fn in TESTS:
        try:
            ok, summary = fn()
        except Exception as e:           # noqa: BLE001
            ok, summary = False, f"ANALYSIS ERROR: {e}"
        all_pass &= ok
        rows.append((name, ok, summary))
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:22s} {summary}")
    print(f"\nOverall: {'ALL PASS' if all_pass else 'FAILURES PRESENT'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())