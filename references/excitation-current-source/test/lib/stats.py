"""Noise / drift statistics and the position-independence comparison.

Stage 6 is the headline acceptance test (TESTING_PLAN Part 2): per-channel noise
at/below the floor, and -- the whole reason the board exists -- **no dependence
on channel/position**, compared directly against the old series-chain data where
noise grew up the chain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from lib.rtd import sensitivity_ohms_per_c


@dataclass
class NoiseStats:
    n: int
    mean: float
    std: float            # rms noise (std dev of samples)
    pp: float             # peak-to-peak
    rms: float            # rms about mean (== std for n>1)
    drift: float          # end-minus-start linear trend over the record

    def as_row(self) -> Dict[str, float]:
        return {
            "n": self.n,
            "mean": self.mean,
            "std": self.std,
            "pp": self.pp,
            "drift": self.drift,
        }


def noise_stats(samples: np.ndarray) -> NoiseStats:
    x = np.asarray(samples, dtype=float)
    x = x[~np.isnan(x)]
    n = x.size
    if n == 0:
        return NoiseStats(0, float("nan"), float("nan"), float("nan"), float("nan"), float("nan"))
    mean = float(np.mean(x))
    std = float(np.std(x, ddof=1)) if n > 1 else 0.0
    pp = float(np.ptp(x)) if n > 1 else 0.0
    # linear drift across the record (slope * span)
    if n > 1:
        idx = np.arange(n)
        slope = float(np.polyfit(idx, x, 1)[0])
        drift = slope * (n - 1)
    else:
        drift = 0.0
    return NoiseStats(n=n, mean=mean, std=std, pp=pp, rms=std, drift=drift)


def resistance_noise_to_temp(
    r_noise_ohms: float, r_at_ohms: float, r0_ohms: float
) -> float:
    """Convert a resistance-noise figure to degC using local dR/dT."""
    s = sensitivity_ohms_per_c(_temp_guess(r_at_ohms, r0_ohms), r0_ohms)
    return r_noise_ohms / s if s else float("nan")


def _temp_guess(r_ohms: float, r0_ohms: float) -> float:
    # cheap linear seed (~0.385 %/K) -- only feeds the sensitivity lookup
    return (r_ohms / r0_ohms - 1.0) / 3.9083e-3


@dataclass
class PositionIndependenceResult:
    per_channel_std: Dict[int, float]
    min_std: float
    max_std: float
    spread_ratio: float          # max/min -- 1.0 == perfectly position-independent
    slope_per_channel: float     # linear fit of std vs channel index
    passed: bool
    tolerance_ratio: float
    notes: List[str] = field(default_factory=list)


def position_independence(
    per_channel_std: Dict[int, float], tolerance_ratio: float = 1.5
) -> PositionIndependenceResult:
    """Verdict on whether per-channel noise is independent of position.

    PASS when the spread (max/min) is within ``tolerance_ratio`` AND the noise
    shows no significant monotonic growth with channel index (the series-chain
    signature). Default 1.5x is a starting gate; tighten against the real floor.
    """
    chans = sorted(per_channel_std)
    stds = np.array([per_channel_std[c] for c in chans], dtype=float)
    notes: List[str] = []
    min_std = float(np.min(stds))
    max_std = float(np.max(stds))
    ratio = max_std / min_std if min_std > 0 else float("inf")
    slope = float(np.polyfit(np.array(chans, dtype=float), stds, 1)[0]) if len(chans) > 1 else 0.0

    spread_ok = ratio <= tolerance_ratio
    # "grows up the chain" check: slope materially positive relative to the mean
    mean_std = float(np.mean(stds))
    growth_ok = (slope * (len(chans) - 1)) <= 0.5 * mean_std if mean_std > 0 else True
    if not spread_ok:
        notes.append(f"noise spread {ratio:.2f}x exceeds {tolerance_ratio:.2f}x tolerance")
    if not growth_ok:
        notes.append("noise grows with channel index (series-chain signature)")

    return PositionIndependenceResult(
        per_channel_std={c: per_channel_std[c] for c in chans},
        min_std=min_std,
        max_std=max_std,
        spread_ratio=ratio,
        slope_per_channel=slope,
        passed=bool(spread_ok and growth_ok),
        tolerance_ratio=tolerance_ratio,
        notes=notes,
    )


@dataclass
class BaselineComparison:
    new_std: Dict[int, float]
    baseline_std: Dict[int, float]
    improvement: Dict[int, float]   # baseline/new per channel (>1 == better)
    new_spread: float
    baseline_spread: float


def compare_to_baseline(
    new_std: Dict[int, float], baseline_std: Dict[int, float]
) -> BaselineComparison:
    """Direct per-channel comparison new board vs old series-chain board."""
    improvement: Dict[int, float] = {}
    for ch, ns in new_std.items():
        bs = baseline_std.get(ch)
        if bs is not None and ns > 0:
            improvement[ch] = bs / ns
    return BaselineComparison(
        new_std=new_std,
        baseline_std=baseline_std,
        improvement=improvement,
        new_spread=_spread(new_std),
        baseline_spread=_spread(baseline_std),
    )


def _spread(d: Dict[int, float]) -> float:
    vals = np.array(list(d.values()), dtype=float)
    vals = vals[vals > 0]
    if vals.size == 0:
        return float("nan")
    return float(np.max(vals) / np.min(vals))