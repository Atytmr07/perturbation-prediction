"""Is there a donor-specific response worth predicting? Variance decomposition of the response.

    python scripts/covid/05_signal_noise.py --config scripts/covid/config_cite_only.json

For every modality, cell type and day d, with delta_i = mean(day d, donor i) - mean(day 0, donor i):
  shared   = ||mean_i delta_i||^2 / n_features              population (shared) response
  donor    = mean_i ||delta_i - mean delta||^2 / n_features   spread of donors around it
  noise    = sampling noise of delta_i, from a split-half of the cells (A vs B):
             Var(delta_i) ~= ||delta_i^A - delta_i^B||^2 / 4 per feature, averaged over donors
  donor_true = max(donor - noise, 0)                           donor-specific signal beyond noise
  donor_share = donor_true / (shared + donor_true)

donor_share ~ 0  -> every donor responds the same; PerturbationMean is already optimal.
donor_share high -> donor-specific response exists; the question is whether it can be
                    predicted from the donor's baseline cells.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import anndata as ad  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from pertbench.data import pseudobulk_sparse  # noqa: E402
from pertbench.datasets import _sparse_norm_select  # noqa: E402

NORM = {"rna": "log1p_cp10k", "adt": "clr", "atac": "binary_log1p_cp10k"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--min-cells", type=int, default=20, help="per half")
    ap.add_argument("--out", default=str(ROOT / "results" / "covid_signal_noise.csv"))
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    n_top = cfg.get("n_top", {})
    rng = np.random.default_rng(0)
    rows = []
    for tname, mods in cfg["files"].items():
        ct_key = cfg["cell_type_key"][tname] if isinstance(cfg["cell_type_key"], dict) else cfg["cell_type_key"]
        for m, path in mods.items():
            x = ad.read_h5ad(path)
            o = x.obs
            half = np.where(rng.random(len(o)) < 0.5, "A", "B")
            X, _ = _sparse_norm_select(x.X, NORM[m], n_top.get(m))
            day = o[cfg["day_key"]].astype(str).to_numpy()
            obs = pd.DataFrame({
                "perturbation": day,
                "cell_type": o[ct_key].astype(str).to_numpy(),
                # donor|half for split-half, donor|all for the full estimate
                "donor": o[cfg["donor_key"]].astype(str).to_numpy(),
            })
            full_obs, full = pseudobulk_sparse(X, obs, min_cells=2 * a.min_cells)
            hobs = obs.assign(donor=obs["donor"] + "|" + half)
            half_obs, halves = pseudobulk_sparse(X, hobs, min_cells=a.min_cells)
            idx_full = {tuple(r): i for i, r in enumerate(full_obs[["perturbation", "cell_type", "donor"]].itertuples(index=False, name=None))}
            idx_half = {tuple(r): i for i, r in enumerate(half_obs[["perturbation", "cell_type", "donor"]].itertuples(index=False, name=None))}
            ctrl = cfg["control_day"]
            for ct in sorted(full_obs["cell_type"].unique()):
                for d in sorted(set(full_obs["perturbation"]) - {ctrl}):
                    deltas, noise = [], []
                    for donor in sorted(full_obs["donor"].unique()):
                        f1, f0 = idx_full.get((d, ct, donor)), idx_full.get((ctrl, ct, donor))
                        if f1 is None or f0 is None:
                            continue
                        deltas.append(full[f1] - full[f0])
                        hs = []
                        for h in "AB":
                            h1, h0 = idx_half.get((d, ct, f"{donor}|{h}")), idx_half.get((ctrl, ct, f"{donor}|{h}"))
                            if h1 is not None and h0 is not None:
                                hs.append(halves[h1] - halves[h0])
                        if len(hs) == 2:
                            noise.append(np.mean((hs[0] - hs[1]) ** 2) / 4)
                    if len(deltas) < 3 or not noise:
                        continue
                    D = np.stack(deltas)
                    mu = D.mean(0)
                    shared = float(np.mean(mu ** 2))
                    donor = float(np.mean(np.sum((D - mu) ** 2, axis=1) / D.shape[1]))
                    nz = float(np.mean(noise))
                    donor_true = max(donor - nz, 0.0)
                    rows.append({"table": tname, "modality": m, "cell_type": ct, "day": d, "n_donors": len(deltas),
                                 "shared": shared, "donor": donor, "noise": nz, "donor_true": donor_true,
                                 "donor_share": donor_true / (shared + donor_true) if shared + donor_true > 0 else np.nan,
                                 "shared_over_noise": shared / nz if nz > 0 else np.nan})
            print(f"[signal/noise] {tname}:{m} bitti")
    res = pd.DataFrame(rows)
    res.to_csv(a.out, index=False)
    with pd.option_context("display.width", 200, "display.max_rows", 200, "display.float_format", "{:.4f}".format):
        print(res.groupby(["modality", "day"])[["shared", "donor", "noise", "donor_true", "donor_share", "shared_over_noise"]].median())
        print()
        print(res.sort_values("donor_true", ascending=False).head(15).to_string(index=False))
    print(f"\n-> {a.out}")


if __name__ == "__main__":
    main()
