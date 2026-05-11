import math
from typing import Iterable, List


def bucket(v: float, vmin: float, vmax: float, n_buckets: int, gamma: float = 1.0) -> int:
    if n_buckets <= 1 or vmax == vmin:
        return 0
    frac = (v - vmin) / (vmax - vmin)
    frac = max(0.0, min(1.0, frac))
    if gamma != 1.0:
        frac = frac ** gamma
    idx = math.floor(frac * n_buckets)
    return max(0, min(n_buckets - 1, idx))


def compute_quantile_thresholds(flat: Iterable[float], n_buckets: int) -> List[float]:
    """Boundary values that split positive data into ``n_buckets - 1`` quantile bands.

    Bucket 0 is reserved for ``v <= 0``, so only nonzero values participate in
    the quantile computation. Returns ``[]`` when the input is too degenerate
    to bin meaningfully (≤1 nonzero value, or fewer than 2 nonzero bands).
    """
    nonzero = sorted(v for v in flat if v > 0)
    n_bands = n_buckets - 1
    if n_bands < 2 or len(nonzero) <= 1:
        return []
    return [nonzero[i * len(nonzero) // n_bands] for i in range(1, n_bands)]


def quantile_bucket(v: float, thresholds: List[float], n_buckets: int) -> int:
    if v <= 0:
        return 0
    if not thresholds:
        return min(1, n_buckets - 1)
    for i, t in enumerate(thresholds):
        if v < t:
            return i + 1
    return n_buckets - 1
