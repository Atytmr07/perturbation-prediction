"""MultiPert variants on THP-1 that let the control cell reach the prediction.

Same data, same random control pairing, same 60/20/20 split and same pretrained encoders as the
original run (results/multipert_original); only the part named by --variant changes:

  original   released model (DualFusionAttention, z = attn * w)
  residual   z = cell + attn * w                      (cell representation added back)
  film       z = cell * (1 + gamma(p)) + beta(p)       (knockout scales/shifts the cell)
  film_wide  film + protein decoder 64 -> 32 -> 4      (instead of 64 -> 2 -> 4)
  film_mmd   film_wide + MMD between predicted and observed cells of each knockout in the batch
             (+ 0.1 x MSE), instead of MSE on randomly paired cells

Writes test_perturb.h5ad / predict.h5ad / preprocessed_*.h5ad in the run folder, so that
02_rescore.py can score it next to NoChange / PerturbationMean.

    .venv-models/Scripts/python scripts/multipert/07_variants.py --variant film
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "external" / "MultiPert" / "code"
sys.path.insert(0, str(CODE))

import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
import torch.optim as optim  # noqa: E402
from torch.utils.data import DataLoader  # noqa: E402

from data_loader import (MultiOmicsDataset, load_and_preprocess_data, sample_data,  # noqa: E402
                         save_to_h5ad, split_dataset)
from models import DualFusionAttention, initialize_models  # noqa: E402
from utils import set_seed  # noqa: E402

ORIG = ROOT / "results" / "multipert_original"
DATA = ROOT / "external" / "MultiPert" / "data"
NAME = "PapalexiSatija2021_eccite_arrayed"


class Residual(DualFusionAttention):
    def forward(self, cell, pert):
        return cell + super().forward(cell, pert)


class FiLM(nn.Module):
    def __init__(self, dim=64):
        super().__init__()
        self.gamma, self.beta = nn.Linear(dim, dim), nn.Linear(dim, dim)
        nn.init.zeros_(self.gamma.weight), nn.init.zeros_(self.gamma.bias)

    def forward(self, cell, pert):
        return cell * (1 + self.gamma(pert)) + self.beta(pert)


def mmd(x, y):
    z = torch.cat([x, y])
    d = torch.cdist(z, z).pow(2)
    med = d.detach().median().clamp_min(1e-6)
    k = sum(torch.exp(-d / (s * med)) for s in (0.5, 1.0, 2.0))
    n = len(x)
    return k[:n, :n].mean() + k[n:, n:].mean() - 2 * k[:n, n:].mean()


def group_mmd(pred, true, labels):
    labels = np.asarray(labels)
    terms = [mmd(pred[labels == p], true[labels == p]) for p in np.unique(labels) if (labels == p).sum() >= 4]
    return torch.stack(terms).mean()


def forward(models, rna, adt, pemb):
    rna_ae, sh_rna, pe_rna, dec_rna, adt_ae, sh_adt, pe_adt, dec_adt, fusion, adv, att = models
    rna_spec, _ = rna_ae.encode(rna)
    rna_sh, adt_sh = sh_rna(rna), sh_adt(adt)
    adt_spec = adt_ae.encoder(adt)
    fused = fusion(rna_sh, adt_sh)
    out_rna = dec_rna(att(torch.cat((rna_spec, fused), 1), pe_rna(pemb)))
    out_adt = dec_adt(att(torch.cat((adt_spec, fused), 1), pe_adt(pemb)))
    return out_rna, out_adt, rna_sh, adt_sh


def recon_loss(variant, out_rna, out_adt, y_rna, y_adt, labels):
    mse = nn.functional.mse_loss(out_rna, y_rna) + nn.functional.mse_loss(out_adt, y_adt)
    if variant != "film_mmd":
        return mse
    return group_mmd(out_rna, y_rna, labels) + group_mmd(out_adt, y_adt, labels) + 0.1 * mse


def train(models, variant, tr, va, device, out, epochs, patience):
    """MultiPert's train_and_validate (alternating discriminator / generator), with a swappable
    reconstruction term."""
    adv = models[9]
    gen = [p for i, m in enumerate(models) if i != 9 for p in m.parameters()]
    opt_g, opt_d = optim.Adam(gen, lr=1e-3), optim.Adam(adv.parameters(), lr=2e-3)
    bce = nn.BCELoss()
    best, bad, best_state = float("inf"), 0, None
    for ep in range(epochs):
        for m in models:
            m.train()
        for rna, adt, lab, y_rna, y_adt, pemb, _, _ in tr:
            rna, adt, y_rna, y_adt, pemb = (t.to(device) for t in (rna, adt, y_rna, y_adt, pemb))
            out_rna, out_adt, rna_sh, adt_sh = forward(models, rna, adt, pemb)
            rec = recon_loss(variant, out_rna, out_adt, y_rna, y_adt, lab)
            ones, zeros, half = (torch.full((len(rna), 1), v, device=device) for v in (1.0, 0.0, 0.5))
            opt_d.zero_grad()
            d_loss = bce(adv(rna_sh.detach()), ones) + bce(adv(adt_sh.detach()), zeros)
            d_loss.backward()
            opt_d.step()
            opt_g.zero_grad()
            g_loss = rec + bce(adv(rna_sh), half) + bce(adv(adt_sh), half)
            g_loss.backward()
            opt_g.step()
        for m in models:
            m.eval()
        with torch.no_grad():
            vl = []
            for rna, adt, lab, y_rna, y_adt, pemb, _, _ in va:
                rna, adt, y_rna, y_adt, pemb = (t.to(device) for t in (rna, adt, y_rna, y_adt, pemb))
                out_rna, out_adt, _, _ = forward(models, rna, adt, pemb)
                vl.append(recon_loss(variant, out_rna, out_adt, y_rna, y_adt, lab).item())
        v = float(np.mean(vl))
        if v < best:
            best, bad, best_state = v, 0, [{k: t.clone() for k, t in m.state_dict().items()} for m in models]
        else:
            bad += 1
        if (ep + 1) % 10 == 0:
            print(f"epoch {ep + 1}: val {v:.4f} (best {best:.4f})", flush=True)
        if bad >= patience:
            print(f"early stop at epoch {ep + 1}", flush=True)
            break
    for m, s in zip(models, best_state):
        m.load_state_dict(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, choices=["original", "residual", "film", "film_wide", "film_mmd"])
    ap.add_argument("--epochs", type=int, default=1000)
    ap.add_argument("--patience", type=int, default=20)
    ap.add_argument("--threads", type=int, default=6)
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    out = ROOT / "results" / f"multipert_variant_{a.variant}"
    out.mkdir(parents=True, exist_ok=True)
    for f in ("preprocessed_rna.h5ad", "preprocessed_adt.h5ad", "rna_ae_pretrained.pth", "adt_ae_pretrained.pth"):
        shutil.copy(ORIG / f, out / f)

    # identical order of random draws as MultiPert's main.py -> same pairing and split
    set_seed(1)
    device = torch.device("cpu")
    rna_c, adt_c, rna_p, adt_p, pinfo, pemb = load_and_preprocess_data(
        str(DATA / f"{NAME}_RNA.h5ad"), str(DATA / f"{NAME}_protein.h5ad"), str(DATA / "pert_embeddings.npz"),
        str(out), device)
    rna_ctrl, adt_ctrl = rna_c.X.toarray(), adt_c.X.toarray()
    rna_pert, adt_pert = rna_p.X.toarray(), adt_p.X.toarray()
    cell_ctrl, cell_pert = np.array(rna_c.obs_names), np.array(rna_p.obs_names)
    s_rna, s_adt, s_cell = [], [], []
    for p in np.unique(pinfo):
        n = int((pinfo == p).sum())
        if n:
            r, d, c = sample_data(rna_ctrl, adt_ctrl, cell_ctrl, n)
            s_rna.append(r), s_adt.append(d), s_cell.append(c)
    # np.asarray: pandas >= 2 no longer indexes a string-indexed Series by position (as in 01_run_original.py)
    ds = MultiOmicsDataset(np.concatenate(s_rna), np.concatenate(s_adt), np.asarray(pinfo), rna_pert, adt_pert, pemb,
                           np.concatenate(s_cell), cell_pert)
    tr_s, va_s, te_s = split_dataset(ds, pinfo)
    tr, va, te = (DataLoader(ds, batch_size=512, sampler=s) for s in (tr_s, va_s, te_s))

    models = initialize_models(tr, rna_ctrl.shape[1], adt_ctrl.shape[1], pemb.shape[1], device, str(out))
    if a.variant == "residual":
        models[10] = Residual(64)
    elif a.variant.startswith("film"):
        models[10] = FiLM(64)
    if a.variant in ("film_wide", "film_mmd"):
        models[7] = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, adt_ctrl.shape[1]))
    train(models, a.variant, tr, va, device, out, a.epochs, a.patience)

    for m in models:
        m.eval()
    keep = {k: [] for k in ("yt", "pt", "ya", "pa", "lab", "cc", "cp", "xr", "xa")}
    with torch.no_grad():
        for rna, adt, lab, y_rna, y_adt, pe, cc, cp in te:
            out_rna, out_adt, _, _ = forward(models, rna, adt, pe)
            for k, v in zip(keep, (y_rna, out_rna, y_adt, out_adt)):
                keep[k].append(v.numpy())
            keep["lab"].extend(lab), keep["cc"].extend(cc), keep["cp"].extend(cp)
            keep["xr"].append(rna.numpy()), keep["xa"].append(adt.numpy())
    cat = {k: np.concatenate(keep[k]) for k in ("yt", "pt", "ya", "pa", "xr", "xa")}
    genes = rna_c.var_names
    save_to_h5ad(cat["xr"], cat["xa"], np.array(keep["lab"]), np.array(keep["cc"]), genes, str(out / "test_control.h5ad"))
    save_to_h5ad(cat["yt"], cat["ya"], np.array(keep["lab"]), np.array(keep["cp"]), genes, str(out / "test_perturb.h5ad"))
    save_to_h5ad(cat["pt"], cat["pa"], np.array(keep["lab"]), np.array(keep["cp"]), genes, str(out / "predict.h5ad"))
    lab = np.array(keep["lab"])
    for m, P, T in (("rna", cat["pt"], cat["yt"]), ("adt", cat["pa"], cat["ya"])):
        sp = np.mean([P[lab == p].std(0).mean() for p in np.unique(lab)])
        st = np.mean([T[lab == p].std(0).mean() for p in np.unique(lab)])
        print(f"{m}: spread of predicted cells within a knockout {sp:.4f} (observed {st:.4f})")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
