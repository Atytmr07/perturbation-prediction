"""MultiPert on the COVID vaccine CITE-seq data (RNA + ADT in the same cells), leave-one-donor-out.

    .venv-models/Scripts/python scripts/multipert/03_covid_lodo.py                       # all 6 folds
    .venv-models/Scripts/python scripts/multipert/03_covid_lodo.py --donors donorA --epochs 30   # quick check
    .venv-models/Scripts/python scripts/multipert/03_covid_lodo.py --pairing random      # original pairing

Uses the released MultiPert model and training loop unchanged (initialize_models, train_and_validate
from external/MultiPert/code). What is adapted to the donor setting:

  * "perturbation" = vaccination day (Day2 / Day11 / Day28), control = Day0. Days are not genes, so the
    perturbation embedding is a one-hot padded to 64 (MultiPert's own fallback for non-gene perturbations).
  * split: one donor is held out; its Day0 cells are the model input, its post-vaccination cells are only
    used for scoring. 15 % of the training pairs are the validation set for MultiPert's early stopping.
  * pairing (--pairing donor, default): every post-vaccination cell is paired with a Day0 cell of the
    *same donor and cell type*. --pairing random reproduces the released code (any control cell).
  * preprocessing as in MultiPert (genes in >=10 cells, CP10k + log1p, top HVG; ADT CP10k + log1p), but
    gene filtering and HVG selection use the training donors only.

Scoring: condition means (donor x day x cell type) from *all* cells, in the same preprocessed space, are
scored with pertbench next to the simple baselines; MultiPert's predicted cells are averaged per condition
and enter through pertbench.external.ExternalPredictions. Distribution distances (MMD, energy) between
predicted and observed test cells are added in a PCA space fitted on training cells.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "external" / "MultiPert" / "code"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

import anndata as ad  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import scanpy as sc  # noqa: E402
import scipy.sparse as sp  # noqa: E402
import torch  # noqa: E402
from torch.utils.data import DataLoader, Dataset  # noqa: E402

from pertbench.data import KEYS, ConditionTable, pseudobulk_sparse  # noqa: E402
from pertbench.external import ExternalPredictions  # noqa: E402
from pertbench.metrics import distribution_metrics  # noqa: E402
from pertbench.models import Additive, ContextRidge, NoChange, PerturbationMean  # noqa: E402
from pertbench.runner import evaluate_split  # noqa: E402
from pertbench.splits import unseen_context  # noqa: E402

DAYS = ["Day2", "Day11", "Day28"]
CONTROL = "Day0"
EMB_DIM = 64


class Pairs(Dataset):
    """Same 8-tuple as MultiPert's MultiOmicsDataset."""

    def __init__(self, rna_c, adt_c, pert, rna_p, adt_p, emb, cell_c, cell_p):
        self.t = (rna_c.astype(np.float32), adt_c.astype(np.float32), np.asarray(pert), rna_p.astype(np.float32),
                  adt_p.astype(np.float32), emb.astype(np.float32), np.asarray(cell_c), np.asarray(cell_p))

    def __len__(self):
        return len(self.t[0])

    def __getitem__(self, i):
        return tuple(x[i] for x in self.t)


def dense(x):
    return np.asarray(x.toarray() if sp.issparse(x) else x, dtype=np.float32)


def day_emb(day: str) -> np.ndarray:
    e = np.zeros(EMB_DIM, np.float32)
    e[DAYS.index(day)] = 1.0
    return e


def log_cp10k(x):
    x = sp.csr_matrix(x, dtype=np.float32)
    lib = np.asarray(x.sum(1)).ravel()
    lib[lib == 0] = 1
    x = sp.diags(1e4 / lib) @ x
    x.data = np.log1p(x.data)
    return x


def predict_cells(models, rna_c, adt_c, emb, device, batch=1024):
    """Forward pass exactly as in MultiPert's main.py test loop."""
    (rna_ae, shared_rna, pert_rna, dec_rna, adt_ae, shared_adt, pert_adt, dec_adt, fusion, _, attn) = models
    for m in models:
        m.eval()
    out_r, out_a = [], []
    with torch.no_grad():
        for s in range(0, len(rna_c), batch):
            r = torch.from_numpy(rna_c[s:s + batch]).to(device)
            a = torch.from_numpy(adt_c[s:s + batch]).to(device)
            e = torch.from_numpy(emb[s:s + batch]).to(device)
            r_spec, _ = rna_ae.encode(r)
            fused = fusion(shared_rna(r), shared_adt(a))
            out_r.append(dec_rna(attn(torch.cat((r_spec, fused), 1), pert_rna(e))).cpu().numpy())
            out_a.append(dec_adt(attn(torch.cat((adt_ae.encoder(a), fused), 1), pert_adt(e))).cpu().numpy())
    return np.concatenate(out_r), np.concatenate(out_a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rna", default=str(ROOT / "data/covid/PBMC_vaccine_CITE__RNA.h5ad"))
    ap.add_argument("--adt", default=str(ROOT / "data/covid/PBMC_vaccine_CITE__ADT.h5ad"))
    ap.add_argument("--cell-type-key", default="celltypel1")
    ap.add_argument("--donors", nargs="*", help="test donors (default: all)")
    ap.add_argument("--pairing", choices=["donor", "random"], default="donor")
    ap.add_argument("--cap", type=int, default=300, help="max training cells per donor x day x cell type")
    ap.add_argument("--n-hvg", type=int, default=2000)
    ap.add_argument("--epochs", type=int, default=400)
    ap.add_argument("--patience", type=int, default=20)
    ap.add_argument("--min-cells", type=int, default=10)
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = Path(a.out or ROOT / "results" / f"multipert_covid_{a.pairing}_{a.cell_type_key}_s{a.seed}")
    out.mkdir(parents=True, exist_ok=True)
    json.dump(vars(a), open(out / "args.json", "w"), indent=2)

    torch.set_num_threads(a.threads)
    from utils import set_seed  # MultiPert's
    from models import initialize_models
    from trainer import train_and_validate
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    rna = ad.read_h5ad(a.rna)
    adt = ad.read_h5ad(a.adt)
    assert (rna.obs_names == adt.obs_names).all()
    obs = pd.DataFrame({"day": rna.obs["timepoint"].astype(str).to_numpy(),
                        "cell_type": rna.obs[a.cell_type_key].astype(str).to_numpy(),
                        "donor": rna.obs["donor"].astype(str).to_numpy()}, index=rna.obs_names.astype(str))
    obs["perturbation"] = np.where(obs["day"] == CONTROL, "control", obs["day"])
    gene_names = np.asarray(rna.var_names.astype(str))
    adt_names = list(map(str, adt.var_names))
    adt_all = dense(log_cp10k(adt.X))                      # MultiPert: CP10k + log1p for protein
    rna_counts = sp.csr_matrix(rna.X, dtype=np.float32)
    donors = sorted(obs["donor"].unique())
    test_donors = a.donors or donors

    rows, timing = [], {}
    for d in test_donors:
        t0 = time.time()
        set_seed(a.seed)
        rng = np.random.default_rng(a.seed)
        fold = out / f"fold_{d}"
        fold.mkdir(exist_ok=True)
        train = (obs["donor"] != d).to_numpy()

        # --- preprocessing, fitted on training donors only
        n_cells_gene = np.asarray((rna_counts[train] > 0).sum(0)).ravel()
        gkeep = np.flatnonzero(n_cells_gene >= 10)
        X = log_cp10k(rna_counts[:, gkeep])
        tmp = ad.AnnData(X[train])
        sc.pp.highly_variable_genes(tmp, n_top_genes=a.n_hvg)
        hv = np.flatnonzero(tmp.var["highly_variable"].to_numpy())
        X = X[:, hv]
        genes = list(gene_names[gkeep][hv])

        # --- training subsample (cap per donor x day x cell type)
        idx = []
        for _, g in obs.groupby(["donor", "day", "cell_type"]).indices.items():
            idx.extend(rng.choice(g, min(len(g), a.cap), replace=False))
        sub = np.zeros(len(obs), bool)
        sub[np.asarray(idx)] = True
        Xd = {}  # dense rows on demand

        def rows_of(mask):
            return dense(X[mask]), adt_all[mask]

        # --- training pairs
        pert_mask = sub & train & (obs["perturbation"] != "control").to_numpy()
        ctrl_mask = sub & train & (obs["perturbation"] == "control").to_numpy()
        p_idx = np.flatnonzero(pert_mask)
        c_pool = obs.iloc[np.flatnonzero(ctrl_mask)]
        if a.pairing == "donor":
            pools = c_pool.groupby(["donor", "cell_type"]).indices
            c_rows = np.flatnonzero(ctrl_mask)
            keep, partner = [], []
            for i in p_idx:
                key = (obs["donor"].iat[i], obs["cell_type"].iat[i])
                if key in pools:
                    keep.append(i)
                    partner.append(c_rows[rng.choice(pools[key])])
            p_idx, partner = np.asarray(keep), np.asarray(partner)
        else:
            partner = rng.choice(np.flatnonzero(ctrl_mask), len(p_idx), replace=True)
        rp, ap_ = dense(X[p_idx]), adt_all[p_idx]
        rc, ac = dense(X[partner]), adt_all[partner]
        pert = obs["perturbation"].to_numpy()[p_idx]
        emb = np.stack([day_emb(p) for p in pert])
        ds = Pairs(rc, ac, pert, rp, ap_, emb, obs.index.to_numpy()[partner], obs.index.to_numpy()[p_idx])
        perm = rng.permutation(len(ds))
        n_val = int(0.15 * len(ds))
        tr_loader = DataLoader(torch.utils.data.Subset(ds, perm[n_val:]), batch_size=512, shuffle=True)
        va_loader = DataLoader(torch.utils.data.Subset(ds, perm[:n_val]), batch_size=512)
        print(f"[{d}] {len(ds)} çift ({a.pairing} eşleşme), {len(genes)} gen, {len(adt_names)} protein", flush=True)

        models = initialize_models(tr_loader, len(genes), len(adt_names), EMB_DIM, device, str(fold))
        train_and_validate(models, tr_loader, va_loader, device, str(fold), epochs=a.epochs, patience=a.patience)

        # --- scoring table from all cells, same preprocessing
        ct_obs = obs[KEYS].reset_index(drop=True)
        pb_obs, M_rna = pseudobulk_sparse(X, ct_obs, min_cells=a.min_cells)
        _, M_adt = pseudobulk_sparse(sp.csr_matrix(adt_all), ct_obs, min_cells=a.min_cells)
        table = ConditionTable(obs=pb_obs, means={"rna": M_rna, "adt": M_adt}, var={"rna": genes, "adt": adt_names})
        split = unseen_context(table, "donor", d)

        # --- MultiPert predictions for the held-out donor
        pred_rows, dist = [], []
        pca_mu = np.asarray(X[train & sub].mean(0)).ravel()
        _, _, vt = np.linalg.svd(dense(X[np.flatnonzero(train & sub)[:5000]]) - pca_mu, full_matrices=False)
        proj = lambda m: (m - pca_mu) @ vt[:30].T  # noqa: E731
        for (p, ct) in table.obs.loc[split.test, ["perturbation", "cell_type"]].itertuples(index=False, name=None):
            cmask = sub & (obs["donor"] == d).to_numpy() & (obs["perturbation"] == "control").to_numpy() \
                & (obs["cell_type"] == ct).to_numpy()
            if cmask.sum() == 0:
                continue
            r_in, a_in = rows_of(cmask)
            pr, pa = predict_cells(models, r_in, a_in, np.tile(day_emb(p), (len(r_in), 1)), device)
            pred_rows.append({"perturbation": p, "cell_type": ct, "donor": d, "modality": "rna",
                              **dict(zip(genes, pr.mean(0)))})
            pred_rows.append({"perturbation": p, "cell_type": ct, "donor": d, "modality": "adt",
                              **dict(zip(adt_names, pa.mean(0)))})
            tmask = (obs["donor"] == d).to_numpy() & (obs["perturbation"] == p).to_numpy() & (obs["cell_type"] == ct).to_numpy()
            if tmask.sum() >= a.min_cells:
                truth = dense(X[np.flatnonzero(tmask)[:1000]])
                dm = distribution_metrics(proj(pr[:1000]), proj(truth))
                dc = distribution_metrics(proj(r_in[:1000]), proj(truth))   # "no change": the input cells
                dist.append({"perturbation": p, "cell_type": ct, "donor": d,
                             "multipert_mmd": dm["mmd"], "multipert_energy": dm["energy"],
                             "nochange_mmd": dc["mmd"], "nochange_energy": dc["energy"],
                             "pred_cell_std": float(pr.std(0).mean()), "true_cell_std": float(truth.std(0).mean())})
        csv = fold / "multipert_predictions.csv"
        pd.DataFrame(pred_rows).to_csv(csv, index=False)
        pd.DataFrame(dist).to_csv(fold / "distribution.csv", index=False)

        for model in [ExternalPredictions(csv, f"MultiPert[{a.pairing}]"), NoChange(), PerturbationMean(),
                      Additive(), ContextRidge()]:
            df = evaluate_split(model, table, split)
            rows.append(df)
        timing[d] = round((time.time() - t0) / 60, 1)
        print(f"[{d}] bitti: {timing[d]} dk", flush=True)
        pd.concat(rows, ignore_index=True).to_csv(out / "per_condition.csv", index=False)

    res = pd.concat(rows, ignore_index=True)
    summ = res.groupby(["modality", "model"])[["pearson_delta", "mse_top20", "direction_acc_top20"]].mean().round(3)
    summ.to_csv(out / "summary.csv")
    dist = pd.concat([pd.read_csv(out / f"fold_{d}" / "distribution.csv") for d in test_donors], ignore_index=True)
    dist.to_csv(out / "distribution_all.csv", index=False)
    json.dump(timing, open(out / "timing_min.json", "w"), indent=2)
    with pd.option_context("display.width", 200):
        print(summ.to_string())
        print("\nDağılım (RNA PCA, ortalama):\n", dist.drop(columns=KEYS).mean().round(3).to_string())
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
