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
