"""Aggregate the CellFlow LODO sweep (02_sweep.sh) over seeds.

Per setting and modality: delta PCC mean (sd) over seeds, and for top-20 MSE the median over
donor folds of CellFlow / baseline. MSE scales differ a lot between synthetic seeds, so the
ratio per fold is reported instead of a mean over seeds.

    .venv-cellflow/Scripts/python scripts/cellflow/03_aggregate.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SWEEP = ROOT / "results" / "cellflow_sweep"
SETTINGS = {  # name: (description, runs)
    "lin_p30": ("linear, 8 donors, 30 perts", [ROOT / "results" / "cellflow_synthetic_lodo"]),
    "nl_p30": ("nonlinear, 8 donors, 30 perts", [SWEEP / f"nl_p30_s{s}" for s in range(3)]),
    "lin_p3": ("linear, 6 donors, 3 perts", [SWEEP / f"lin_p3_s{s}" for s in range(3)]),
    "nl_p3": ("nonlinear, 6 donors, 3 perts", [SWEEP / f"nl_p3_s{s}" for s in range(3)]),
}
MODELS = ["PerturbationMean", "ContextRidge", "CellFlow"]


def complete(run, n_donors):
    """True if every fold of the run finished (runs stopped by the time budget are partial)."""
    if not (run / "per_condition.csv").exists():
        return False
    return pd.read_csv(run / "per_condition.csv", usecols=["donor"])["donor"].nunique() == n_donors


def main():
    rows = []
    for name, (desc, runs) in SETTINGS.items():
        runs = [r for r in runs if complete(r, 8 if "p30" in name else 6)]
        r = pd.concat([pd.read_csv(p / "per_condition.csv").assign(seed=i) for i, p in enumerate(runs)])
        r = r[r["model"].isin(MODELS)]
        pcc = r.groupby(["seed", "modality", "model"])["pearson_delta"].mean().unstack()
        fold = r.groupby(["seed", "donor", "modality", "model"])["mse_top20"].mean().unstack()
        wins = fold.idxmin(axis=1)
        for m in sorted(r["modality"].unique()):
            row = {"setting": name, "description": desc, "seeds": len(runs), "modality": m}
            for model in MODELS:
                row[f"pcc_{model}"] = round(pcc.xs(m, level="modality")[model].mean(), 3)
                row[f"pcc_sd_{model}"] = round(pcc.xs(m, level="modality")[model].std(), 3)
                row[f"wins_{model}"] = int((wins.xs(m, level="modality") == model).sum())
            f = fold.xs(m, level="modality")
            row["mse_ratio_CF_vs_PM"] = round((f["CellFlow"] / f["PerturbationMean"]).median(), 2)
            row["mse_ratio_CF_vs_CR"] = round((f["CellFlow"] / f["ContextRidge"]).median(), 2)
            row["n_folds"] = len(f)
            rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(SWEEP / "aggregate.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
