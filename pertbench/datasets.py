"""Loaders for public perturbation datasets (scPerturb harmonised h5ad files on Zenodo).

Files are cached under data/. Download them with scripts/download_data.py.
Each loader maps the dataset's own columns onto perturbation / cell_type / donor.
When a dataset has no donors, a replicate or batch column stands in, and the
loader says so, because "unseen replicate" is a much easier task than "unseen donor".
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from pertbench.data import PerturbData, _dense, _normalise_counts

DATA = Path(__file__).resolve().parents[1] / "data"
ZENODO = "https://zenodo.org/records/10044268/files/{}?download=1"

FILES = {
    "papalexi2021": ["PapalexiSatija2021_eccite_RNA.h5ad", "PapalexiSatija2021_eccite_protein.h5ad"],
    "frangieh2021_protein": ["FrangiehIzar2021_protein.h5ad"],
    "frangieh2021": ["FrangiehIzar2021_RNA.h5ad", "FrangiehIzar2021_protein.h5ad"],   # RNA file is 1.5 GB
    "norman2019": ["NormanWeissman2019_filtered.h5ad"],                               # 0.7 GB, RNA only
}


def _read(name: str):
    import anndata as ad
    p = DATA / name
    if not p.exists():
        raise FileNotFoundError(f"{p} missing; run: python scripts/download_data.py {name}")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ad.read_h5ad(p)


def _hvg(x: np.ndarray, names: list[str], k: int, force: set[str] = frozenset()):
    """Top-k variance features, always keeping `force` (e.g. perturbation targets)."""
    order = np.argsort(-x.var(axis=0))
    keep = set(order[:k]) | {i for i, n in enumerate(names) if n in force}
    keep = np.array(sorted(keep))
    return x[:, keep], [names[i] for i in keep]


def _sparse_log1p_cp10k_hvg(x, names: list[str], k: int, force: set[str]):
    """log1p(CP10k) + top-k variance selection without densifying the full matrix."""
    import scipy.sparse as sp
    x = sp.csr_matrix(x, dtype=np.float32)
    lib = np.asarray(x.sum(axis=1)).ravel()
    lib[lib == 0] = 1
    x = sp.diags(1e4 / lib) @ x
    x.data = np.log1p(x.data)
    mean = np.asarray(x.mean(axis=0)).ravel()
    var = np.asarray(x.multiply(x).mean(axis=0)).ravel() - mean ** 2
    keep = set(np.argsort(-var)[:k]) | {i for i, n in enumerate(names) if n in force}
    keep = np.array(sorted(keep))
    return _dense(x[:, keep]), [names[i] for i in keep]


def _build(mods: dict, obs: pd.DataFrame, norm: dict, n_hvg: int, targets: set[str], mask) -> PerturbData:
    X, var = {}, {}
    for m, a in mods.items():
        names = list(map(str, a.var_names))
        if m == "rna" and norm[m] == "log1p_cp10k" and a.shape[1] > n_hvg:
            x, names = _sparse_log1p_cp10k_hvg(a.X[mask], names, n_hvg, targets)
        else:
            x = _normalise_counts(_dense(a.X[mask]), norm[m])
        X[m], var[m] = x.astype(np.float32), names
    perts = sorted(set(obs["perturbation"]) - {"control"})
    meta = pd.DataFrame({"perturbation": perts, "target_gene": perts})
    return PerturbData(X=X, obs=obs.reset_index(drop=True), var=var, pert_meta=meta)


def papalexi2021(n_hvg: int = 2000) -> PerturbData:
    """ECCITE-seq in THP-1 (Papalexi et al., Nat Genet 2021): RNA + 4 surface proteins, 25 target genes.

    Guides are collapsed to target genes. There is one cell line and no donors;
    the `donor` column holds the experimental replicate (rep1/rep3/rep4).
    """
    rna, prot = (_read(f) for f in FILES["papalexi2021"])
    o = rna.obs
    pert = o["perturbation"].astype(str).str.replace(r"g\d+$", "", regex=True)
    rep = o["hto"].astype(str).str.replace(r"-.*$", "", regex=True)
    mask = rep.isin(["rep1", "rep3", "rep4"]).to_numpy()
    obs = pd.DataFrame({"perturbation": pert[mask].to_numpy(), "cell_type": "THP-1", "donor": rep[mask].to_numpy()})
    return _build({"rna": rna, "protein": prot}, obs, {"rna": "log1p_cp10k", "protein": "clr"},
                  n_hvg, set(obs["perturbation"]), mask)


def frangieh2021_protein() -> PerturbData:
    """Perturb-CITE-seq in patient-derived melanoma cells (Frangieh et al., Nat Genet 2021), protein only.

    `cell_type` holds the culture condition (Control / IFN-gamma / TIL co-culture),
    so the unseen_cell_type split asks: predict the response under a new stimulus.
    Only single-guide cells are kept; isotype controls are dropped.
    """
    (prot,) = (_read(f) for f in FILES["frangieh2021_protein"])
    o = prot.obs
    mask = (o["nperts"] <= 1).to_numpy()
    keep_var = [not re.search(r"IgG", v) for v in prot.var_names]
    prot = prot[:, keep_var]
    cond = o["perturbation_2"].astype(str).map(lambda s: "IFNg" if s.startswith("IFN") else s)
    obs = pd.DataFrame({"perturbation": o["perturbation"].astype(str)[mask].to_numpy(),
                        "cell_type": cond[mask].to_numpy(), "donor": "patient"})
    return _build({"protein": prot}, obs, {"protein": "clr"}, 0, set(), mask)


def _sparse_norm_select(X, kind: str, n_top: int | None):
    """Normalise a cells x features count matrix sparsely and keep the n_top most variable features."""
    import scipy.sparse as sp
    X = sp.csr_matrix(X, dtype=np.float32)
    if kind == "binary_log1p_cp10k":   # ATAC peaks: binarise first
        X.data[:] = 1.0
        kind = "log1p_cp10k"
    if kind == "log1p_cp10k":
        lib = np.asarray(X.sum(axis=1)).ravel()
        lib[lib == 0] = 1
        X = sp.diags(1e4 / lib) @ X
        X.data = np.log1p(X.data)
    elif kind == "clr":                # ADT
        Xd = np.log1p(X.toarray())
        X = sp.csr_matrix(Xd - Xd.mean(axis=1, keepdims=True))
    elif kind != "none":
        raise ValueError(kind)
    keep = None
    if n_top and n_top < X.shape[1]:
        mean = np.asarray(X.mean(axis=0)).ravel()
        var = np.asarray(X.multiply(X).mean(axis=0)).ravel() - mean ** 2
        keep = np.sort(np.argsort(-var)[:n_top])
        X = X[:, keep]
    return X, keep


def covid_vaccine(files: dict, donor_key: str, day_key: str, cell_type_key: str, control_day: str,
                  norm: dict | None = None, n_top: dict | None = None, min_cells: int = 10,
                  cell_type_map: dict | None = None, train_donors: list[str] | None = None):
    """Zhang et al. 2023 (Nat Immunol) COVID vaccination: 6 donors x day 0/2/10/28,
    CITE-seq (RNA+ADT) and ASAP-seq (ATAC+ADT) on different aliquots of the same samples.

    files: {table: {modality: h5ad path}}, e.g.
        {"cite": {"rna": ".../PBMC_vaccine_CITE__RNA.h5ad", "adt": ".../PBMC_vaccine_CITE__ADT.h5ad"},
         "asap": {"atac": ".../PBMC_vaccine_ASAP__peaks.h5ad", "adt": ".../PBMC_vaccine_ASAP__ADT.h5ad"}}
    Returns one ConditionTable with modalities rna, cite_adt, atac, asap_adt (pseudobulk per
    donor x day x cell type). Day `control_day` becomes the control.

    train_donors: if given, feature selection (top-variance features) uses only these donors' cells,
    so the held-out donor does not leak into preprocessing.
    """
    import anndata as ad
    from pertbench.data import ConditionTable, merge_tables, pseudobulk_sparse
    norm = {"rna": "log1p_cp10k", "adt": "clr", "atac": "binary_log1p_cp10k", **(norm or {})}
    n_top = {"rna": 3000, "atac": 20000, **(n_top or {})}
    tables = {}
    for tname, mods in files.items():
        means, var, obs0 = {}, {}, None
        for m, path in mods.items():
            a = ad.read_h5ad(path)
            o = a.obs
            ct = o[cell_type_key].astype(str)
            if cell_type_map:
                ct = ct.map(lambda s: cell_type_map.get(s, s))
            day = o[day_key].astype(str)
            obs = pd.DataFrame({"perturbation": np.where(day == str(control_day), "control", "day" + day),
                                "cell_type": ct.to_numpy(), "donor": o[donor_key].astype(str).to_numpy()})
            names = np.asarray(a.var_names.astype(str))
            if train_donors is None:
                X, keep = _sparse_norm_select(a.X, norm[m], n_top.get(m))
            else:  # pick features on training donors only, then apply to everyone
                in_train = obs["donor"].isin(train_donors).to_numpy()
                _, keep = _sparse_norm_select(a.X[in_train], norm[m], n_top.get(m))
                X, _ = _sparse_norm_select(a.X, norm[m], None)
                if keep is not None:
                    X = X[:, keep]
            names = names[keep] if keep is not None else names
            pb_obs, M = pseudobulk_sparse(X, obs, min_cells=min_cells)
            if obs0 is None:
                obs0 = pb_obs
            elif not obs0[["perturbation", "cell_type", "donor"]].equals(pb_obs[["perturbation", "cell_type", "donor"]]):
                raise ValueError(f"{tname}: modalities do not share cells/metadata")
            means[m], var[m] = M, list(names)
        tables[tname] = ConditionTable(obs=obs0, means=means, var=var)
    return merge_tables(tables) if len(tables) > 1 else next(iter(tables.values()))


LOADERS = {"papalexi2021": papalexi2021, "frangieh2021_protein": frangieh2021_protein}
