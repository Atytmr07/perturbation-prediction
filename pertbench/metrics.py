"""Condition-level metrics.

Raw-profile Pearson is reported but is known to be uninformative (it is ~0.99
for the no-change baseline). The delta-based metrics are the ones to read.
"""

from __future__ import annotations

import numpy as np


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a - a.mean(), b - b.mean()
    den = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / den) if den > 0 else np.nan


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    den = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / den) if den > 0 else np.nan


def condition_metrics(pred: np.ndarray, true: np.ndarray, ctrl: np.ndarray, top_k: int = 20) -> dict[str, float]:
    dp, dt = pred - ctrl, true - ctrl
    top = np.argsort(-np.abs(dt))[: min(top_k, len(dt))]
    return {
        "mse": float(np.mean((pred - true) ** 2)),
        "pearson": _pearson(pred, true),
        "pearson_delta": _pearson(dp, dt),
        "cosine_delta": _cosine(dp, dt),
        f"mse_top{top_k}": float(np.mean((dp[top] - dt[top]) ** 2)),
        f"pearson_delta_top{top_k}": _pearson(dp[top], dt[top]),
        f"direction_acc_top{top_k}": float(np.mean(np.sign(dp[top]) == np.sign(dt[top]))),
    }


def delta_norm(true: np.ndarray, ctrl: np.ndarray) -> float:
    """Effect size of the true response; useful to stratify results by strong vs weak perturbations."""
    return float(np.linalg.norm(true - ctrl))


# ---------------------------------------------------------------------------
# Distribution-level metrics: compare predicted and observed *cells*, not means.
# Use them for models that generate cells (MultiPert, flow/OT models). Inputs are
# (n_cells, n_features) arrays, ideally in a low-dimensional space (PCA/latent),
# since kernel distances degrade in thousands of raw gene dimensions.
# ---------------------------------------------------------------------------

def _subsample(x: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    return x if len(x) <= n else x[rng.choice(len(x), n, replace=False)]


def _sq_dists(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    d = (a * a).sum(1)[:, None] + (b * b).sum(1)[None, :] - 2 * a @ b.T
    return np.maximum(d, 0.0)


def mmd_rbf(x: np.ndarray, y: np.ndarray, bandwidths: tuple[float, ...] | None = None,
            max_cells: int = 2000, seed: int = 0) -> float:
    """Unbiased squared MMD with a sum of RBF kernels.

    Bandwidths default to multiples of the median pairwise distance of the pooled sample,
    so the value is comparable across conditions of the same dataset.
    """
    rng = np.random.default_rng(seed)
    x, y = _subsample(np.asarray(x, float), max_cells, rng), _subsample(np.asarray(y, float), max_cells, rng)
    if len(x) < 2 or len(y) < 2:
        return np.nan
    dxx, dyy, dxy = _sq_dists(x, x), _sq_dists(y, y), _sq_dists(x, y)
    if bandwidths is None:
        med = np.median(np.concatenate([dxx[np.triu_indices(len(x), 1)], dxy.ravel()]))
        bandwidths = tuple(med * s for s in (0.25, 1.0, 4.0)) if med > 0 else (1.0,)
    k = lambda d: sum(np.exp(-d / (2 * h)) for h in bandwidths)  # noqa: E731
    kxx, kyy, kxy = k(dxx), k(dyy), k(dxy)
    n, m = len(x), len(y)
    return float((kxx.sum() - np.trace(kxx)) / (n * (n - 1))
                 + (kyy.sum() - np.trace(kyy)) / (m * (m - 1))
                 - 2 * kxy.mean())


def energy_distance(x: np.ndarray, y: np.ndarray, max_cells: int = 2000, seed: int = 0) -> float:
    """Energy distance 2E|X-Y| - E|X-X'| - E|Y-Y'| (0 iff the distributions are equal)."""
    rng = np.random.default_rng(seed)
    x, y = _subsample(np.asarray(x, float), max_cells, rng), _subsample(np.asarray(y, float), max_cells, rng)
    if len(x) < 2 or len(y) < 2:
        return np.nan
    dxy = np.sqrt(_sq_dists(x, y)).mean()
    dxx = np.sqrt(_sq_dists(x, x)).sum() / (len(x) * (len(x) - 1))
    dyy = np.sqrt(_sq_dists(y, y)).sum() / (len(y) * (len(y) - 1))
    return float(2 * dxy - dxx - dyy)


def distribution_metrics(pred_cells: np.ndarray, true_cells: np.ndarray, **kw) -> dict[str, float]:
    return {"mmd": mmd_rbf(pred_cells, true_cells, **kw), "energy": energy_distance(pred_cells, true_cells, **kw)}
