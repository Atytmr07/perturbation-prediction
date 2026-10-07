"""Seurat .rds -> assay başına bir h5ad (R gerekmez).

    python scripts/covid/03_convert.py data/covid/PBMC_vaccine_CITE.rds --assays RNA ADT
    python scripts/covid/03_convert.py data/covid/PBMC_vaccine_ASAP.rds --assays ATAC ADT:scale.data

Assay adlarını 02_inspect_rds.py çıktısından alın. Katman varsayılan olarak ham sayımlar
("counts"); bir assay için farklı katman `ASSAY:katman` ile seçilir. ASAP'ta ADT'nin sadece
`scale.data` katmanı var, ama içinde ölçeklenmiş değer değil **ham sayımlar** duruyor
(tam sayı; hücre toplamları meta.data'daki nCount_ADT ile birebir aynı). Bu yüzden
yükleyicide CITE ADT'si gibi CLR ile normalize edilir. Her assay data/covid/<dosya>__<assay>.h5ad olur; hücre metadata'sı
hepsinde aynıdır. Kullanılan katman adata.uns["seurat_layer"] içine yazılır.
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
    ap.add_argument("--assays", nargs="+", required=True, help="ASSAY veya ASSAY:katman")
    ap.add_argument("--layer", default="counts", help="katmanı belirtilmeyen assay'ler için")
    ap.add_argument("--no-compress", action="store_true", help="büyük ATAC için daha hızlı yazım")
    a = ap.parse_args()

    robj = py8rds.parse_rds(a.rds)
    stem = Path(a.rds).with_suffix("")
    for spec in a.assays:
        assay, _, layer = spec.partition(":")
        layer = layer or a.layer
        ad = assay_to_adata(robj, assay, layer)
        for c in ad.obs.columns:  # h5ad yazımı için kategorik/str temizliği
            if ad.obs[c].dtype == object:
                ad.obs[c] = ad.obs[c].astype(str)
        ad.uns["seurat_layer"] = layer
        out = Path(f"{stem}__{assay}.h5ad")
        ad.write_h5ad(out, compression=None if a.no_compress else "gzip")
        print(f"{assay} [{layer}]: {ad.shape[0]} hücre x {ad.shape[1]} özellik -> {out}", flush=True)


if __name__ == "__main__":
    main()
