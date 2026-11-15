"""Small, dependency-free statistics helpers (seeded, deterministic)."""
from __future__ import annotations

import math
import random


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def wilson(k: int, n: int, z: float = 1.96):
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def _pct(sorted_vals, q):
    if not sorted_vals:
        return float("nan")
    i = q * (len(sorted_vals) - 1)
    lo, hi = math.floor(i), math.ceil(i)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (i - lo)


def bootstrap_mean_ci(values, n_boot=10000, seed=0, alpha=0.05):
    """Percentile bootstrap CI of the mean, resampling clusters (e.g. bug instances)."""
    values = list(values)
    if not values:
        return (float("nan"), float("nan"), float("nan"))
    rng = random.Random(seed)
    n = len(values)
    boots = sorted(mean(values[rng.randrange(n)] for _ in range(n)) for _ in range(n_boot))
    return (mean(values), _pct(boots, alpha / 2), _pct(boots, 1 - alpha / 2))


def paired_bootstrap_diff(a, b, n_boot=10000, seed=0, alpha=0.05):
    """Mean of (a_i - b_i) with a percentile bootstrap CI over the paired clusters."""
    assert len(a) == len(b)
    return bootstrap_mean_ci([x - y for x, y in zip(a, b)], n_boot, seed, alpha)


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value from the discordant counts b and c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def holm(pvals):
    """Holm-Bonferroni adjusted p-values, in the input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adj[i] = running
    return adj


def brier(conf, outcome):
    return mean((c - o) ** 2 for c, o in zip(conf, outcome))


def ece(conf, outcome, bins=10):
    """Expected calibration error with equal-width bins."""
    n = len(conf)
    if n == 0:
        return float("nan")
    total = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, c in enumerate(conf) if (lo <= c < hi) or (b == bins - 1 and c == 1.0)]
        if idx:
            total += len(idx) / n * abs(mean(conf[i] for i in idx) - mean(outcome[i] for i in idx))
    return total
