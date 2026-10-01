"""Download scPerturb h5ad files from Zenodo (record 10044268) into data/.

    python scripts/download_data.py papalexi2021 frangieh2021_protein
    python scripts/download_data.py PapalexiSatija2021_eccite_RNA.h5ad

figshare links used by pertpy sit behind a bot challenge and fail from scripts;
Zenodo works with plain HTTP.
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pertbench.datasets import DATA, FILES, ZENODO  # noqa: E402


def fetch(fname: str):
    DATA.mkdir(exist_ok=True)
    out = DATA / fname
    if out.exists() and out.stat().st_size > 0:
        print(f"have {out}")
        return
    print(f"downloading {fname} ...")
    tmp = out.with_suffix(".part")
    urllib.request.urlretrieve(ZENODO.format(fname), tmp)
    tmp.rename(out)
    print(f"  -> {out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    for arg in sys.argv[1:] or ["papalexi2021"]:
        for f in FILES.get(arg, [arg]):
            fetch(f)
