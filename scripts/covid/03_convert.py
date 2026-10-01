"""Seurat .rds -> assay başına bir h5ad (R gerekmez).

    python scripts/covid/03_convert.py data/covid/PBMC_vaccine_CITE.rds --assays RNA ADT
    python scripts/covid/03_convert.py data/covid/PBMC_vaccine_ASAP.rds --assays ADT peaks

Assay adlarını 02_inspect_rds.py çıktısından alın (ör. ATAC için "peaks", "ATAC" veya
gene activity için "GeneActivity" olabilir). Her assay data/covid/<dosya>__<assay>.h5ad olur;
hücre metadata'sı hepsinde aynıdır. Varsayılan katman ham sayımlar ("counts").
"""

from __future__ import annotations

import argparse
from pathlib import Path

import py8rds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rds")
    ap.add_argument("--assays", nargs="+", required=True)
    ap.add_argument("--layer", default="counts")
    a = ap.parse_args()

    robj = py8rds.parse_rds(a.rds)
    stem = Path(a.rds).with_suffix("")
    for assay in a.assays:
        ad = py8rds.seurat2adata(robj, assay=assay, layer=a.layer)
        for c in ad.obs.columns:  # h5ad yazımı için kategorik/str temizliği
            if ad.obs[c].dtype == object:
                ad.obs[c] = ad.obs[c].astype(str)
        out = Path(f"{stem}__{assay}.h5ad")
        ad.write_h5ad(out, compression="gzip")
        print(f"{assay}: {ad.shape[0]} hücre x {ad.shape[1]} özellik -> {out}")


if __name__ == "__main__":
    main()
