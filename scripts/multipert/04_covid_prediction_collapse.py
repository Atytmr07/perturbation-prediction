"""Diagnose prediction collapse in COVID MultiPert leave-one-donor-out outputs.

Expected fold layout (default):
    <outputs-root>/output_lodo_celltype_<donor>_full/
        test_perturb.h5ad
        predict.h5ad

The script reports two complementary diagnostics:
1) feature-wise variance across predicted cells versus true Day28 cells;
2) permutation sensitivity: shuffle prediction rows across cells and recompute
   flattened PCC/MSE. If cell-specific predictions carry information, shuffling
   should hurt performance. If predictions are effectively constant, it will not.
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


def flat_metrics(true, pred):
    true = dense(true).astype(np.float32)
    pred = dense(pred).astype(np.float32)
    return pearsonr(true.ravel(), pred.ravel())[0], mean_squared_error(true, pred)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outputs-root", type=Path, required=True)
    ap.add_argument(
        "--pattern",
        default="output_lodo_celltype_{donor}_full",
        help="fold directory pattern relative to --outputs-root",
    )
    ap.add_argument("--donors", nargs="*", default=DEFAULT_DONORS)
    ap.add_argument("--n-perm", type=int, default=20)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--round-decimals", type=int, default=5)
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    out_dir = args.out_dir or args.outputs_root
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    variance_rows = []
    permutation_rows = []

    for donor in args.donors:
        fold = args.outputs_root / args.pattern.format(donor=donor)
        true = sc.read_h5ad(fold / "test_perturb.h5ad")
        pred = sc.read_h5ad(fold / "predict.h5ad")

        true_rna = dense(true.X)
        pred_rna = dense(pred.X)
        true_adt = dense(true.obsm["adt"])
        pred_adt = dense(pred.obsm["adt"])

        if true_rna.shape != pred_rna.shape or true_adt.shape != pred_adt.shape:
            raise ValueError(f"Shape mismatch in {donor}")

        true_rna_var = np.var(true_rna, axis=0)
        pred_rna_var = np.var(pred_rna, axis=0)
        true_adt_var = np.var(true_adt, axis=0)
        pred_adt_var = np.var(pred_adt, axis=0)

        def safe_ratio(num, den):
            return float(num / den) if den > 0 else np.nan

        variance_rows.append(
            {
                "donor": donor,
                "RNA_TrueMeanVariance": float(np.mean(true_rna_var)),
                "RNA_PredMeanVariance": float(np.mean(pred_rna_var)),
                "RNA_VarianceRatio": safe_ratio(np.mean(pred_rna_var), np.mean(true_rna_var)),
                "RNA_TrueMeanFeatureStd": float(np.mean(np.std(true_rna, axis=0))),
                "RNA_PredMeanFeatureStd": float(np.mean(np.std(pred_rna, axis=0))),
                "RNA_UniquePredRowsRounded": int(
                    len(np.unique(np.round(pred_rna, args.round_decimals), axis=0))
                ),
                "RNA_MaxDiff_Cell0_Cell1": float(
                    np.max(np.abs(pred_rna[0] - pred_rna[1])) if len(pred_rna) > 1 else np.nan
                ),
                "RNA_MaxDiff_Cell0_Cell100": float(
                    np.max(np.abs(pred_rna[0] - pred_rna[100])) if len(pred_rna) > 100 else np.nan
                ),
                "ADT_TrueMeanVariance": float(np.mean(true_adt_var)),
                "ADT_PredMeanVariance": float(np.mean(pred_adt_var)),
                "ADT_VarianceRatio": safe_ratio(np.mean(pred_adt_var), np.mean(true_adt_var)),
                "ADT_TrueMeanFeatureStd": float(np.mean(np.std(true_adt, axis=0))),
                "ADT_PredMeanFeatureStd": float(np.mean(np.std(pred_adt, axis=0))),
                "ADT_UniquePredRowsRounded": int(
                    len(np.unique(np.round(pred_adt, args.round_decimals), axis=0))
                ),
                "ADT_MaxDiff_Cell0_Cell1": float(
                    np.max(np.abs(pred_adt[0] - pred_adt[1])) if len(pred_adt) > 1 else np.nan
                ),
                "ADT_MaxDiff_Cell0_Cell100": float(
                    np.max(np.abs(pred_adt[0] - pred_adt[100])) if len(pred_adt) > 100 else np.nan
                ),
            }
        )

        rna_orig_pcc, rna_orig_mse = flat_metrics(true_rna, pred_rna)
        adt_orig_pcc, adt_orig_mse = flat_metrics(true_adt, pred_adt)

        rna_perm_pcc, rna_perm_mse = [], []
        adt_perm_pcc, adt_perm_mse = [], []
        for _ in range(args.n_perm):
            idx = rng.permutation(len(pred_rna))
            pcc_, mse_ = flat_metrics(true_rna, pred_rna[idx])
            rna_perm_pcc.append(pcc_)
            rna_perm_mse.append(mse_)
            pcc_, mse_ = flat_metrics(true_adt, pred_adt[idx])
            adt_perm_pcc.append(pcc_)
            adt_perm_mse.append(mse_)

        permutation_rows.append(
            {
                "donor": donor,
                "RNA_Original_PCC": rna_orig_pcc,
                "RNA_Shuffled_PCC": float(np.mean(rna_perm_pcc)),
                "RNA_PCC_Drop": float(rna_orig_pcc - np.mean(rna_perm_pcc)),
                "RNA_Original_MSE": rna_orig_mse,
                "RNA_Shuffled_MSE": float(np.mean(rna_perm_mse)),
                "ADT_Original_PCC": adt_orig_pcc,
                "ADT_Shuffled_PCC": float(np.mean(adt_perm_pcc)),
                "ADT_PCC_Drop": float(adt_orig_pcc - np.mean(adt_perm_pcc)),
                "ADT_Original_MSE": adt_orig_mse,
                "ADT_Shuffled_MSE": float(np.mean(adt_perm_mse)),
            }
        )

    variance = pd.DataFrame(variance_rows)
    permutation = pd.DataFrame(permutation_rows)

    variance.to_csv(out_dir / "LODO_prediction_variance.csv", index=False)
    permutation.to_csv(out_dir / "LODO_prediction_permutation.csv", index=False)

    print("\n=== VARIANCE: PER DONOR ===")
    print(variance.to_string(index=False))
    print("\n=== VARIANCE: MEAN ===")
    print(variance.drop(columns="donor").mean(numeric_only=True).to_string())

    print("\n=== PERMUTATION: PER DONOR ===")
    print(permutation.to_string(index=False))
    print("\n=== PERMUTATION: MEAN ===")
    print(permutation.drop(columns="donor").mean(numeric_only=True).to_string())


if __name__ == "__main__":
    main()
