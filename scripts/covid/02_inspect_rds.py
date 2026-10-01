"""Seurat .rds dosyasının içini R olmadan listele: assay'ler, katmanlar, metadata sütunları.

    python scripts/covid/02_inspect_rds.py data/covid/PBMC_vaccine_CITE.rds
    python scripts/covid/02_inspect_rds.py data/covid/PBMC_vaccine_ASAP.rds

Çıktı data/covid/<ad>.inspect.json dosyasına da yazılır. 03_convert.py'deki sütun adlarını
(donör, gün, hücre tipi) buna bakarak seçin. Büyük dosyada okuma birkaç dakika ve
dosya boyutunun ~3-4 katı RAM ister.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import py8rds


def names(robj):
    n = robj.get("names") if robj is not None else None
    return list(n.value) if n is not None and n.value is not None else []


def main(path: str):
    r = py8rds.parse_rds(path)
    out = {"file": path, "assays": {}, "reductions": names(r.get("reductions")), "meta": {}}
    for a in names(r.get("assays")):
        assay = r.get(["assays", a])
        slots = [x[0] for x in assay.attributes if isinstance(x, list) and isinstance(x[0], str)]
        layers = names(assay.get("layers"))
        out["assays"][a] = {"slots": slots, "layers(Assay5)": layers}
    meta = py8rds.as_data_frame(r.get("meta.data"))
    out["n_cells"] = int(meta.shape[0])
    for c in meta.columns:
        s = meta[c]
        nun = int(s.nunique())
        out["meta"][c] = {"dtype": str(s.dtype), "n_unique": nun,
                          "examples": [str(v) for v in s.astype(str).value_counts().index[:8]] if nun <= 200 else []}
    dest = Path(path).with_suffix(".inspect.json")
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False)[:6000])
    print(f"\n-> {dest}")


if __name__ == "__main__":
    main(sys.argv[1])
