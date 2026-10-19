"""Cell-type pseudobulk diagnostics and simple baselines for COVID MultiPert LODO.

This script evaluates the held-out donor at donor x cell-type pseudobulk level and
compares MultiPert with two population baselines:

* MeanDay28: equal-donor mean Day28 profile from training donors for the same cell type.
* MeanDelta: held-out donor Day0 profile + equal-donor mean (Day28-Day0) from training donors
  for the same cell type.

It reports both absolute Day28 profile metrics and response-delta metrics, where
Delta = Day28 - held-out donor Day0 for the same cell type.

Expected inputs:
* prepared RNA/ADT h5ad files containing raw counts and metadata columns donor,
  perturbation, and celltypel1 (or --cell-type-key);
* fold outputs containing test_perturb.h5ad and predict.h5ad.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import scanpy as sc
from scipy import sparse
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error

DEFAULT_DONORS = ["donorA", "donorB", "donorE", "donorF", "donorJ", "donorM"]


def dense(x):
    return x.toarray() if sparse.issparse(x) else np.asarray(x)


def log_cp10k(x):
    x = sparse.csr_matrix(x, dtype=np.float32)
    lib = np.asarray(x.sum(1)).ravel()
    lib[lib == 0] = 1
    x = sparse.diags(1e4 / lib) @ x
    x.data = np.log1p(x.data)
    return x


def mean_vec(x):
    if sparse.issparse(x):
        return np.asarray(x.mean(axis=0)).ravel()
    return np.asarray(x).mean(axis=0)


def pcc(a, b):
    a = np.asarray(a).ravel()
    b = np.asarray(b).ravel()
    if np.std(a) < 1e-8 or np.std(b) < 1e-8:
        return np.nan
    return pearsonr(a, b)[0]


def mse(a, b):
    return mean_squared_error(np.asarray(a).ravel(), np.asarray(b).ravel())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rna", type=Path, required=True)
    ap.add_argument("--adt", type=Path, required=True)
    ap.add_argument("--outputs-root", type=Path, required=True)
    ap.add_argument("--pattern", default="output_lodo_celltype_{donor}_full")
    ap.add_argument("--donors", nargs="*", default=DEFAULT_DONORS)
    ap.add_argument("--cell-type-key", default="celltypel1")
    ap.add_argument("--donor-key", default="donor")
    ap.add_argument("--perturbation-key", default="perturbation")
    ap.add_argument("--control", default="control")
    ap.add_argument("--treated", default="vaccine")
    ap.add_argument("--min-test-cells", type=int, default=50)
    ap.add_argument("--min-train-cells", type=int, default=20)
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    out_dir = args.out_dir or args.outputs_root
    out_dir.mkdir(parents=True, exist_ok=True)

    rna_all = sc.read_h5ad(args.rna)
    adt_all = sc.read_h5ad(args.adt)
    if not rna_all.obs_names.equals(adt_all.obs_names):
        raise ValueError("RNA and ADT obs_names must match")

    rows = []

    for heldout in args.donors:
        fold = args.outputs_root / args.pattern.format(donor=heldout)
        true = sc.read_h5ad(fold / "test_perturb.h5ad")
        pred = sc.read_h5ad(fold / "predict.h5ad")

        genes = list(true.var_names.astype(str))
        missing = [g for g in genes if g not in rna_all.var_names]
        if missing:
            raise ValueError(f"{heldout}: {len(missing)} prediction genes not found in prepared RNA")

        rna_fold = rna_all[:, genes].copy()
        rna_fold.X = log_cp10k(rna_fold.X)
        adt_fold = adt_all.copy()
        adt_fold.X = log_cp10k(adt_fold.X)

        if true.obsm["adt"].shape[1] != adt_fold.n_vars:
            raise ValueError(f"{heldout}: ADT feature count mismatch")

        target_ids = true.obs_names.astype(str)
        target_meta = rna_fold.obs.reindex(target_ids)
        if target_meta.isnull().all(axis=1).any():
            raise ValueError(f"{heldout}: target cell IDs missing from prepared RNA")

        target_types = target_meta[args.cell_type_key].astype(str).to_numpy()
        true_rna = dense(true.X)
        pred_rna = dense(pred.X)
        true_adt = dense(true.obsm["adt"])
        pred_adt = dense(pred.obsm["adt"])

        donor = rna_fold.obs[args.donor_key].astype(str).to_numpy()
        ctype = rna_fold.obs[args.cell_type_key].astype(str).to_numpy()
        perturb = rna_fold.obs[args.perturbation_key].astype(str).to_numpy()
        train_donors = sorted(set(donor) - {heldout})

        for ct in sorted(np.unique(target_types)):
            target_mask = target_types == ct
            heldout_ctrl_mask = (
                (donor == heldout)
                & (ctype == ct)
                & (perturb == args.control)
            )
            if target_mask.sum() < args.min_test_cells or heldout_ctrl_mask.sum() < args.min_test_cells:
                continue

            true_rna_pb = true_rna[target_mask].mean(axis=0)
            pred_rna_pb = pred_rna[target_mask].mean(axis=0)
            true_adt_pb = true_adt[target_mask].mean(axis=0)
            pred_adt_pb = pred_adt[target_mask].mean(axis=0)

            heldout_rna_day0 = mean_vec(rna_fold[heldout_ctrl_mask].X)
            heldout_adt_day0 = mean_vec(adt_fold[heldout_ctrl_mask].X)

            day28_rna, day28_adt = [], []
            delta_rna, delta_adt = [], []

            for d in train_donors:
                ctrl_mask = (donor == d) & (ctype == ct) & (perturb == args.control)
                trt_mask = (donor == d) & (ctype == ct) & (perturb == args.treated)
                if ctrl_mask.sum() < args.min_train_cells or trt_mask.sum() < args.min_train_cells:
                    continue

                r0 = mean_vec(rna_fold[ctrl_mask].X)
                r1 = mean_vec(rna_fold[trt_mask].X)
                a0 = mean_vec(adt_fold[ctrl_mask].X)
                a1 = mean_vec(adt_fold[trt_mask].X)
                day28_rna.append(r1)
                day28_adt.append(a1)
                delta_rna.append(r1 - r0)
                delta_adt.append(a1 - a0)

            if len(delta_rna) < 2:
                continue

            mean_day28_rna = np.mean(day28_rna, axis=0)
            mean_day28_adt = np.mean(day28_adt, axis=0)
            mean_delta_rna = np.mean(delta_rna, axis=0)
            mean_delta_adt = np.mean(delta_adt, axis=0)

            baseline_delta_rna_day28 = heldout_rna_day0 + mean_delta_rna
            baseline_delta_adt_day28 = heldout_adt_day0 + mean_delta_adt

            true_rna_delta = true_rna_pb - heldout_rna_day0
            pred_rna_delta = pred_rna_pb - heldout_rna_day0
            true_adt_delta = true_adt_pb - heldout_adt_day0
            pred_adt_delta = pred_adt_pb - heldout_adt_day0

            rows.append(
                {
                    "donor": heldout,
                    "cell_type": ct,
                    "n_day0": int(heldout_ctrl_mask.sum()),
                    "n_day28": int(target_mask.sum()),
                    "RNA_PB_PCC_MultiPert": pcc(true_rna_pb, pred_rna_pb),
                    "RNA_PB_MSE_MultiPert": mse(true_rna_pb, pred_rna_pb),
                    "RNA_PB_PCC_MeanDay28": pcc(true_rna_pb, mean_day28_rna),
                    "RNA_PB_MSE_MeanDay28": mse(true_rna_pb, mean_day28_rna),
                    "RNA_PB_PCC_MeanDelta": pcc(true_rna_pb, baseline_delta_rna_day28),
                    "RNA_PB_MSE_MeanDelta": mse(true_rna_pb, baseline_delta_rna_day28),
                    "RNA_Delta_PCC_MultiPert": pcc(true_rna_delta, pred_rna_delta),
                    "RNA_Delta_PCC_MeanDay28": pcc(true_rna_delta, mean_day28_rna - heldout_rna_day0),
                    "RNA_Delta_PCC_MeanDelta": pcc(true_rna_delta, mean_delta_rna),
                    "ADT_PB_PCC_MultiPert": pcc(true_adt_pb, pred_adt_pb),
                    "ADT_PB_MSE_MultiPert": mse(true_adt_pb, pred_adt_pb),
                    "ADT_PB_PCC_MeanDay28": pcc(true_adt_pb, mean_day28_adt),
                    "ADT_PB_MSE_MeanDay28": mse(true_adt_pb, mean_day28_adt),
                    "ADT_PB_PCC_MeanDelta": pcc(true_adt_pb, baseline_delta_adt_day28),
                    "ADT_PB_MSE_MeanDelta": mse(true_adt_pb, baseline_delta_adt_day28),
                    "ADT_Delta_PCC_MultiPert": pcc(true_adt_delta, pred_adt_delta),
                    "ADT_Delta_PCC_MeanDay28": pcc(true_adt_delta, mean_day28_adt - heldout_adt_day0),
                    "ADT_Delta_PCC_MeanDelta": pcc(true_adt_delta, mean_delta_adt),
                }
            )

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No donor x cell-type groups passed the cell-count thresholds")

    metrics = [c for c in df.columns if c not in {"donor", "cell_type", "n_day0", "n_day28"}]
    summary = pd.DataFrame(
        {
            "Mean": df[metrics].mean(),
            "Median": df[metrics].median(),
            "Std": df[metrics].std(),
        }
    )
    delta_cols = [
        "RNA_Delta_PCC_MultiPert",
        "RNA_Delta_PCC_MeanDay28",
        "RNA_Delta_PCC_MeanDelta",
        "ADT_Delta_PCC_MultiPert",
        "ADT_Delta_PCC_MeanDay28",
        "ADT_Delta_PCC_MeanDelta",
    ]
    by_celltype = df.groupby("cell_type")[delta_cols].mean()

    df.to_csv(out_dir / "LODO_celltype_baselines.csv", index=False)
    summary.to_csv(out_dir / "LODO_celltype_baselines_summary.csv")
    by_celltype.to_csv(out_dir / "LODO_celltype_baselines_by_celltype.csv")

    print("\n=== DONOR x CELL TYPE ===")
    print(df.to_string(index=False))
    print("\n=== OVERALL SUMMARY ===")
    print(summary.to_string())
    print("\n=== MEAN DELTA PCC BY CELL TYPE ===")
    print(by_celltype.to_string())


if __name__ == "__main__":
    main()
