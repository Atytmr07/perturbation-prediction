"""Seurat .rds -> one h5ad per assay (no R needed).

    python scripts/covid/03_convert.py data/covid/PBMC_vaccine_CITE.rds --assays RNA ADT
    python scripts/covid/03_convert.py data/covid/PBMC_vaccine_ASAP.rds --assays ATAC ADT:scale.data

Take the assay names from the 02_inspect_rds.py output. The default layer is raw counts
("counts"); another layer is chosen per assay with `ASSAY:layer`. In ASAP the ADT assay only
has a `scale.data` layer, but it holds **raw counts**, not scaled values (integers; per-cell
totals equal nCount_ADT in meta.data), so the loader CLR-normalises it like the CITE ADT.
Each assay becomes data/covid/<file>__<assay>.h5ad with the same cell metadata. The layer
used is stored in adata.uns["seurat_layer"].
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import py8rds


def assay_to_adata(robj, assay: str, layer: str):
    """seurat2adata, with a fallback that skips the assay's feature metadata.

    In PBMC_vaccine_ASAP.rds the ADT assay's meta.features cannot be parsed by py8rds
    (AttributeError in as_data_frame). The matrix and the cell metadata are fine, so read
    those directly and leave var empty (feature names still come from the matrix dimnames).
    """
    try:
        return py8rds.seurat2adata(robj, assay=assay, layer=layer)
    except Exception as e:  # noqa: BLE001
        logging.warning("seurat2adata(%s, %s) failed (%s); reading matrix + meta.data directly", assay, layer, e)
    names = [str(v) for v in robj.get(["assays", "names"]).value]
    mat = robj.get(["assays", names.index(assay), layer])
    if mat is None:
        raise ValueError(f"assay {assay!r} has no layer {layer!r}")
    ad = py8rds.as_anndata(mat)
    obs = py8rds.as_data_frame(robj.get("meta.data"))
    if py8rds.is_default_index(obs) and obs.shape[0] == ad.shape[0]:
        obs.index = ad.obs_names
    ad.obs = obs.loc[ad.obs_names]
    return ad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rds")
    ap.add_argument("--assays", nargs="+", required=True, help="ASSAY or ASSAY:layer")
    ap.add_argument("--layer", default="counts", help="for assays given without a layer")
    ap.add_argument("--no-compress", action="store_true", help="faster writing for the large ATAC assay")
    a = ap.parse_args()

    robj = py8rds.parse_rds(a.rds)
    stem = Path(a.rds).with_suffix("")
    for spec in a.assays:
        assay, _, layer = spec.partition(":")
        layer = layer or a.layer
        ad = assay_to_adata(robj, assay, layer)
        for c in ad.obs.columns:  # object columns -> str, so h5ad can write them
            if ad.obs[c].dtype == object:
                ad.obs[c] = ad.obs[c].astype(str)
        ad.uns["seurat_layer"] = layer
        out = Path(f"{stem}__{assay}.h5ad")
        ad.write_h5ad(out, compression=None if a.no_compress else "gzip")
        print(f"{assay} [{layer}]: {ad.shape[0]} cells x {ad.shape[1]} features -> {out}", flush=True)


if __name__ == "__main__":
    main()
