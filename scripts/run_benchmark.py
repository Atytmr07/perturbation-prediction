"""Command-line entry point.

    python scripts/run_benchmark.py --dataset synthetic
    python scripts/run_benchmark.py --dataset papalexi2021
    python scripts/run_benchmark.py --dataset h5ad --path data/x.h5ad --pert-key gene --control NT --donor-key donor
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from pertbench import datasets, make_synthetic, pseudobulk  # noqa: E402
from pertbench.models import default_models  # noqa: E402
from pertbench.runner import run, skill_vs_baseline, summarise  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="synthetic", choices=["synthetic", *datasets.LOADERS, "h5ad"])
    ap.add_argument("--path")
    ap.add_argument("--pert-key")
    ap.add_argument("--control", default="control")
    ap.add_argument("--cell-type-key")
    ap.add_argument("--donor-key")
    ap.add_argument("--splits", nargs="+", default=None)
    ap.add_argument("--min-cells", type=int, default=10)
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    if a.dataset == "synthetic":
        data = make_synthetic(seed=a.seed)
    elif a.dataset == "h5ad":
        import anndata as ad
        from pertbench.data import from_anndata
        data = from_anndata({"rna": ad.read_h5ad(a.path)}, a.pert_key, a.control, a.cell_type_key, a.donor_key,
                            normalise={"rna": "log1p_cp10k"}, n_top_features={"rna": 2000})
    else:
        data = datasets.LOADERS[a.dataset]()
    print("[pertbench]", data.summary())

    ct = pseudobulk(data, min_cells=a.min_cells)
    splits = a.splits or [s for s, col in [("random", None), ("unseen_perturbation", None),
                                           ("unseen_cell_type", "cell_type"), ("unseen_donor", "donor")]
                          if col is None or ct.obs[col].nunique() > 1]
    res = run(default_models(ct.modalities), ct, splits)

    out = Path(a.out) / a.dataset
    out.mkdir(parents=True, exist_ok=True)
    res.to_csv(out / "per_condition.csv", index=False)
    summ = summarise(res)
    summ.to_csv(out / "summary.csv", index=False)
    skill = skill_vs_baseline(res)
    skill.to_csv(out / "skill_vs_PerturbationMean.csv")
    with pd.option_context("display.width", 200, "display.max_columns", 20, "display.max_rows", 200):
        print(summ.to_string(index=False))
        print("\nSkill vs PerturbationMean on top-20 MSE (>0 = better):")
        print(skill.to_string())
    print(f"\n[pertbench] wrote {out}")


if __name__ == "__main__":
    main()
