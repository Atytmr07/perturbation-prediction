"""Re-create MultiPert's GEARS perturbation embeddings, optionally without one knockout.

MultiPert's get_perturb.ipynb trains GEARS on all ten THP-1 knockouts and saves the GNN-refined
perturbation embeddings. For a leakage-free unseen-knockout test, the held-out knockout must not be
in GEARS' training data. This script trains GEARS (official package; hidden_size 64, 20 epochs, as
in the notebook) with --holdout removed and saves the embeddings the same way the forward pass
builds them: pert_emb weights refined by the SGConv layers over the GO graph.

Deviation from the notebook: GEARS uses MultiPert's 5,000 HVGs (results/multipert_original/
preprocessed_rna.h5ad) instead of all genes, to keep CPU training time reasonable. So the gene list
in the output differs from the shipped pert_embeddings.npz.

Setup: pip install cell-gears torch_geometric. With pandas >= 2, GEARS'
PertData.create_cell_graph_dataset uses `adata_.obs['condition_name'][0]`, which no longer falls back
to positional access on a string index (same issue as MultiPert's data loader). This script patches
that one expression to `.iloc[0]` in memory at import time; the installed package is not modified.
Likewise, newer scipy rejects a pandas boolean Series as a sparse row index in GEARS.__init__, so
that mask is converted with `.to_numpy()` in memory.

    .venv-models/Scripts/python scripts/multipert/08_gears_embeddings.py --holdout ATF2
    .venv-models/Scripts/python scripts/multipert/08_gears_embeddings.py --holdout none
"""
from __future__ import annotations

import argparse
import pickle
import shutil
import sys
import time
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "data" / "gears_thp1"
KNOCKOUTS = ["ATF2", "CAV1", "ETV7", "IFNGR1", "IFNGR2", "IRF1", "IRF7", "MARCH8", "CD274", "STAT2"]


def patch_gears():
    """In-memory pandas >= 2 fix for PertData.create_cell_graph_dataset (see module docstring)."""
    import inspect
    import textwrap

    import gears.pertdata as gp
    src = textwrap.dedent(inspect.getsource(gp.PertData.create_cell_graph_dataset))
    old = "adata_.obs['condition_name'][0]"
    assert old in src, "GEARS source changed; check the pandas fix"
    ns = {}
    exec(compile(src.replace(old, "adata_.obs['condition_name'].iloc[0]"), gp.__file__, "exec"), gp.__dict__, ns)
    gp.PertData.create_cell_graph_dataset = ns["create_cell_graph_dataset"]

    # newer scipy rejects a pandas boolean Series as a sparse-matrix row index (GEARS.__init__)
    import gears.gears as gg
    src = textwrap.dedent(inspect.getsource(gg.GEARS.__init__))
    old = "self.adata.X[self.adata.obs.condition == 'ctrl']"
    assert old in src, "GEARS source changed; check the scipy fix"
    ns = {}
    exec(compile(src.replace(old, "self.adata.X[(self.adata.obs.condition == 'ctrl').to_numpy()]"),
                 gg.__file__, "exec"), gg.__dict__, ns)
    gg.GEARS.__init__ = ns["__init__"]

    # pandas >= 2.2/3 drops the grouping column from groupby().apply(); GEARS' custom GO graph then
    # loses 'target'. Same top-(k+1) edges per target, keeping the column (stable sort = nlargest 'first').
    import gears.utils as gu
    orig = gu.get_similarity_network

    def get_similarity_network(network_type, adata, threshold, k, data_path, data_name, split, seed,
                               train_gene_set_size, set2conditions, default_pert_graph=True, pert_list=None):
        if network_type != "go" or default_pert_graph:
            return orig(network_type, adata, threshold, k, data_path, data_name, split, seed,
                        train_gene_set_size, set2conditions, default_pert_graph, pert_list)
        df = gu.make_GO(data_path, pert_list, data_name)
        return (df.sort_values("importance", ascending=False, kind="mergesort")
                  .groupby("target").head(k + 1).reset_index(drop=True))

    gg.get_similarity_network = get_similarity_network


def build_adata():
    a = ad.read_h5ad(ROOT / "results" / "multipert_original" / "preprocessed_rna.h5ad")
    pert = a.obs["perturbation"].astype(str).replace({"PDL1": "CD274"})
    cond = np.where(pert == "control", "ctrl", pert + "+ctrl")
    g = ad.AnnData(a.X.copy(), obs=pd.DataFrame({"condition": cond, "cell_type": "THP-1"}, index=a.obs_names),
                   var=pd.DataFrame({"gene_name": a.var_names.astype(str)}, index=a.var_names.astype(str)))
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--holdout", required=True, help="gene to leave out of GEARS training, or 'none'")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--threads", type=int, default=6)
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    from gears import GEARS, PertData
    patch_gears()

    hold = None if a.holdout.lower() == "none" else ("CD274" if a.holdout == "PDL1" else a.holdout)
    name = f"thp1g_wo_{hold or 'none'}".lower()
    WORK.mkdir(parents=True, exist_ok=True)
    g = build_adata()
    # Fixed gene set for the GO graph: the 5,000 genes plus every knockout target, so the held-out gene
    # is a node of the graph (its vector then comes only from its GO neighbours) even without its cells.
    gene_set = WORK / "gene_set_hvg_plus_knockouts.pkl"
    with open(gene_set, "wb") as f:
        pickle.dump(sorted(set(g.var["gene_name"]) | set(KNOCKOUTS)), f)
    if hold:
        g = g[g.obs["condition"] != f"{hold}+ctrl"].copy()
    pd_ = PertData(str(WORK), gene_set_path=str(gene_set), default_pert_graph=False)
    if not (WORK / name).exists():
        pd_.new_data_process(dataset_name=name, adata=g)
    pd_.load(data_path=(WORK / name).as_posix())  # GEARS takes the dataset name from the text after the last "/"
    conds = sorted(set(pd_.adata.obs["condition"]))
    split = {"train": conds, "val": ["ctrl"], "test": ["ctrl"]}
    with open(WORK / f"{name}_split.pkl", "wb") as f:
        pickle.dump(split, f)
    pd_.prepare_split(split="custom", split_dict_path=str(WORK / f"{name}_split.pkl"), seed=1)
    pd_.get_dataloader(batch_size=32, test_batch_size=128)

    torch.manual_seed(1)
    t0 = time.time()
    m = GEARS(pd_, device="cpu", weight_bias_track=False, proj_name="pertnet", exp_name="pertnet")
    # the GO graph depends only on the gene set (same for all folds): reuse GEARS' cached edge list
    shared, mine = ROOT / "data" / "go_essential_thp1g_shared.csv", ROOT / "data" / f"go_essential_{name}.csv"
    if shared.exists() and not mine.exists():
        shutil.copy(shared, mine)
    m.model_initialize(hidden_size=64)
    if mine.exists() and not shared.exists():
        shutil.copy(mine, shared)
    m.dataloader.pop("test_loader", None)  # test set is 'ctrl' only; GEARS' post-training analysis is not needed
    t1 = time.time()
    print(f"[gears] graphs ready after {(t1 - t0) / 60:.1f} min", flush=True)
    m.train(epochs=a.epochs, lr=1e-3)
    print(f"[gears] {a.epochs} epochs in {(time.time() - t1) / 60:.1f} min", flush=True)
    net = m.best_model if getattr(m, "best_model", None) is not None else m.model
    net.eval()
    with torch.no_grad():
        e = net.pert_emb(torch.arange(net.num_perts))
        for i, layer in enumerate(net.sim_layers):
            e = layer(e, net.G_sim, net.G_sim_weight)
            if i < net.num_layers - 1:
                e = e.relu()
    out = ROOT / "results" / "gears_embeddings" / f"pert_embeddings_wo_{hold or 'none'}.npz"
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, pert_embeddings=e.numpy(), pert_list=np.array(pd_.pert_names))
    print(f"{len(pd_.pert_names)} genes, {(time.time() - t0) / 60:.1f} min -> {out}")


if __name__ == "__main__":
    main()
