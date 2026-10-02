"""Re-score MultiPert's test predictions with pertbench metrics, next to simple baselines.

    .venv/Scripts/python scripts/multipert/02_rescore.py [--run results/multipert_original]

Per perturbation p (test cells only):
  paper_pcc       MultiPert's own metric: Pearson over the flattened cells x genes matrix of raw values
  pearson_delta,  pertbench delta metrics on condition means (vs. the control mean)
  mse_top20, ...
  mmd / energy    distribution distance between predicted and observed test cells (PCA space)

Models compared on the same test cells:
  MultiPert          the released model
  NoChange           control mean (predicts no response)
  PerturbationMean   mean of p's own *training* cells. MultiPert's split puts cells of every
                     perturbation in train and test, so this is the honest reference for that split
  LeaveOutMean       control + average response of the *other* perturbations (what a model
                     can do without having seen p; relevant for unseen-perturbation claims)
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import anndata as ad  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from pertbench.metrics import condition_metrics, distribution_metrics  # noqa: E402

warnings.filterwarnings("ignore")


def dense(x):
    return np.asarray(x.toarray() if hasattr(x, "toarray") else x, dtype=np.float64)


def paper_pcc(true_cells, pred_cells):
    a, b = true_cells.ravel(), pred_cells.ravel()
    return float(np.corrcoef(a, b)[0, 1])


def pca_fit(X, k=30):
    mu = X.mean(0)
    _, _, vt = np.linalg.svd(X - mu, full_matrices=False)
    return lambda Y: (Y - mu) @ vt[:k].T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=str(ROOT / "results" / "multipert_original"))
    a = ap.parse_args()
    run = Path(a.run)

    rna_all = ad.read_h5ad(run / "preprocessed_rna.h5ad")
    adt_all = ad.read_h5ad(run / "preprocessed_adt.h5ad")
    test = ad.read_h5ad(run / "test_perturb.h5ad")
    pred = ad.read_h5ad(run / "predict.h5ad")
    assert (test.obs_names == pred.obs_names).all()

    pert_all = rna_all.obs["perturbation"].astype(str).to_numpy()
    X = {"rna": dense(rna_all.X), "adt": dense(adt_all.X)}
    T = {"rna": dense(test.X), "adt": dense(test.obsm["adt"])}
    P = {"rna": dense(pred.X), "adt": dense(pred.obsm["adt"])}
    tp = test.obs["perturb"].astype(str).to_numpy()

    is_test = rna_all.obs_names.isin(test.obs_names)
    is_ctrl = pert_all == "control"
    train = ~is_test & ~is_ctrl
    ctrl = {m: X[m][is_ctrl].mean(0) for m in X}
    perts = sorted(set(tp))
    train_mean = {m: {p: X[m][train & (pert_all == p)].mean(0) for p in perts} for m in X}
    proj = {m: pca_fit(X[m][is_ctrl | train], k=min(30, X[m].shape[1])) for m in X}

    rows = []
    for m in ("rna", "adt"):
        for p in perts:
            sel = tp == p
            true_mean = T[m][sel].mean(0)
            others = [train_mean[m][q] - ctrl[m] for q in perts if q != p]
            preds = {
                "MultiPert": P[m][sel].mean(0),
                "NoChange": ctrl[m],
                "PerturbationMean": train_mean[m][p],
                "LeaveOutMean": ctrl[m] + np.mean(others, axis=0),
            }
            # cell-level stand-ins for the distribution metrics
            cells = {
                "MultiPert": P[m][sel],
                "NoChange": X[m][is_ctrl],
                "PerturbationMean": X[m][train & (pert_all == p)],
            }
            for name, mu in preds.items():
                r = condition_metrics(mu, true_mean, ctrl[m])
                r.update(modality=m, perturbation=p, model=name, n_test_cells=int(sel.sum()))
                if name == "MultiPert":
                    r["paper_pcc"] = paper_pcc(T[m][sel], P[m][sel])
                if name in cells:
                    r.update(distribution_metrics(proj[m](cells[name]), proj[m](T[m][sel])))
                rows.append(r)
    res = pd.DataFrame(rows)
    res.to_csv(run / "rescored_per_perturbation.csv", index=False)

    cols = ["paper_pcc", "pearson", "pearson_delta", "pearson_delta_top20", "mse_top20",
            "direction_acc_top20", "mmd", "energy"]
    summ = res.groupby(["modality", "model"])[cols].mean().round(3)
    summ.to_csv(run / "rescored_summary.csv")
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(summ.to_string())
    print(f"\n-> {run / 'rescored_summary.csv'}")


if __name__ == "__main__":
    main()
