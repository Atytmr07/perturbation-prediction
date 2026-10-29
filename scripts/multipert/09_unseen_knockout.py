"""Leave-one-knockout-out test of MultiPert on THP-1 (the paper's 'unseen perturbation' setting).

For each of the 9 knockouts k: all cells of k are held out; MultiPert is trained on the 8 other
knockouts (80/20 train/validation) and predicts k's cells from k's perturbation embedding.

  --emb shipped   the pert_embeddings.npz shipped with MultiPert (GEARS trained on all knockouts,
                  so k's vector has seen k's data: possible leakage)
  --emb gears     embeddings from 08_gears_embeddings.py with k left out of GEARS training
  --variant       original | film_mmdmean (see 07_variants.py)

Scored against baselines that use no information about k's response:
  NoChange       control mean
  LeaveOutMean   control mean + average effect of the other 8 knockouts (training cells)

    .venv-models/Scripts/python scripts/multipert/09_unseen_knockout.py --variant original --emb gears
"""
from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("v07", ROOT / "scripts" / "multipert" / "07_variants.py")
v07 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v07)  # also puts MultiPert's code folder on sys.path

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
from torch.utils.data import DataLoader, SubsetRandomSampler  # noqa: E402

from data_loader import MultiOmicsDataset, load_and_preprocess_data, sample_data  # noqa: E402
from models import initialize_models  # noqa: E402
from pertbench.metrics import condition_metrics, distribution_metrics  # noqa: E402
from utils import set_seed  # noqa: E402

KNOCKOUTS = ["ATF2", "CAV1", "ETV7", "IFNGR1", "IRF1", "IRF7", "MARCH8", "PDL1", "STAT2"]


def pca_fit(X, k=30):
    mu = X.mean(0)
    _, _, vt = np.linalg.svd(X - mu, full_matrices=False)
    return lambda Y: (Y - mu) @ vt[:k].T


def run_fold(k, a, out):
    fold = out / f"fold_{k}"
    fold.mkdir(parents=True, exist_ok=True)
    for f in ("preprocessed_rna.h5ad", "preprocessed_adt.h5ad", "rna_ae_pretrained.pth", "adt_ae_pretrained.pth"):
        shutil.copy(v07.ORIG / f, fold / f)
    emb = (v07.DATA / "pert_embeddings.npz" if a.emb == "shipped" else
           ROOT / "results" / "gears_embeddings" / f"pert_embeddings_wo_{'CD274' if k == 'PDL1' else k}.npz")
    set_seed(1)
    rna_c, adt_c, rna_p, adt_p, pinfo, pemb = load_and_preprocess_data(
        str(v07.DATA / f"{v07.NAME}_RNA.h5ad"), str(v07.DATA / f"{v07.NAME}_protein.h5ad"), str(emb),
        str(fold), torch.device("cpu"))
    pinfo = np.asarray(pinfo)
    rna_ctrl, adt_ctrl = rna_c.X.toarray(), adt_c.X.toarray()
    rna_pert, adt_pert = rna_p.X.toarray(), adt_p.X.toarray()
    cell_ctrl, cell_pert = np.array(rna_c.obs_names), np.array(rna_p.obs_names)
    # same per-knockout random control pairing as MultiPert's main.py
    s_rna, s_adt, s_cell = [], [], []
    for p in np.unique(pinfo):
        r, d, c = sample_data(rna_ctrl, adt_ctrl, cell_ctrl, int((pinfo == p).sum()))
        s_rna.append(r), s_adt.append(d), s_cell.append(c)
    ds = MultiOmicsDataset(np.concatenate(s_rna), np.concatenate(s_adt), pinfo, rna_pert, adt_pert, pemb,
                           np.concatenate(s_cell), cell_pert)
    rng = np.random.default_rng(1)
    other = np.flatnonzero(pinfo != k)
    rng.shuffle(other)
    n_val = int(0.2 * len(other))
    va_idx, tr_idx, te_idx = other[:n_val], other[n_val:], np.flatnonzero(pinfo == k)
    tr, va, te = (DataLoader(ds, batch_size=512, sampler=SubsetRandomSampler(i)) for i in (tr_idx, va_idx, te_idx))

    models = initialize_models(tr, rna_ctrl.shape[1], adt_ctrl.shape[1], pemb.shape[1], torch.device("cpu"), str(fold))
    if a.variant == "film_mmdmean":
        models[10] = v07.FiLM(64)
        models[7] = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, adt_ctrl.shape[1]))
    v07.train(models, a.variant, tr, va, torch.device("cpu"), fold, a.epochs, a.patience)
    for m in models:
        m.eval()
    P = {"rna": [], "adt": []}
    with torch.no_grad():
        for rna, adt, _, _, _, pe, _, _ in te:
            o_rna, o_adt, _, _ = v07.forward(models, rna, adt, pe)
            P["rna"].append(o_rna.numpy()), P["adt"].append(o_adt.numpy())
    P = {m: np.concatenate(v) for m, v in P.items()}

    X = {"rna": (rna_ctrl, rna_pert), "adt": (adt_ctrl, adt_pert)}
    rows = []
    for m, (C, Y) in X.items():
        ctrl = C.mean(0)
        true = Y[pinfo == k]
        effects = [Y[pinfo == q].mean(0) - ctrl for q in np.unique(pinfo) if q != k]
        loo = ctrl + np.mean(effects, axis=0)
        proj = pca_fit(np.vstack([C, Y[pinfo != k]]), k=min(30, C.shape[1]))
        preds = {"MultiPert": (P[m].mean(0), P[m]), "NoChange": (ctrl, C),
                 "LeaveOutMean": (loo, C + (loo - ctrl))}
        for name, (mu, cells) in preds.items():
            r = condition_metrics(mu, true.mean(0), ctrl)
            r.update(distribution_metrics(proj(cells), proj(true)))
            r.update(knockout=k, modality=m, model=name,
                     spread=float(cells.std(0).mean()) if name == "MultiPert" else np.nan)
            rows.append(r)
    pd.DataFrame(rows).to_csv(fold / "metrics.csv", index=False)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="original", choices=["original", "film_mmdmean"])
    ap.add_argument("--emb", default="gears", choices=["shipped", "gears"])
    ap.add_argument("--knockouts", nargs="*", default=KNOCKOUTS)
    ap.add_argument("--epochs", type=int, default=1000)
    ap.add_argument("--patience", type=int, default=20)
    ap.add_argument("--threads", type=int, default=6)
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    out = ROOT / "results" / f"multipert_unseen_ko_{a.variant}_{a.emb}"
    rows = []
    for k in a.knockouts:
        print(f"=== {k}", flush=True)
        rows += run_fold(k, a, out)
    res = pd.DataFrame(rows)
    res.to_csv(out / "per_knockout.csv", index=False)
    cols = ["pearson_delta", "mse_top20", "direction_acc_top20", "mmd", "spread"]
    summ = res.groupby(["modality", "model"])[cols].mean().round(3)
    summ.to_csv(out / "summary.csv")
    print(summ.to_string())
    print(f"-> {out}")


if __name__ == "__main__":
    main()
