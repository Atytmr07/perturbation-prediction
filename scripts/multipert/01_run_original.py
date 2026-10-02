"""Run MultiPert exactly as released (external/MultiPert, Papalexi 2021 arrayed ECCITE-seq, THP-1).

    .venv-models/Scripts/python scripts/multipert/01_run_original.py [--epochs 1000] [--threads 12]

Outputs go to results/multipert_original/ (predict.h5ad, test_perturb.h5ad, test_control.h5ad,
preprocessed_*.h5ad, metrics_rna.csv, metrics_adt.csv, model_best_*.pth). The repo's own
early stopping (patience 20 on validation loss) decides when training stops.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "external" / "MultiPert" / "code"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=1000)
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--out", default=str(ROOT / "results" / "multipert_original"))
    a = ap.parse_args()
    if not CODE.exists():
        sys.exit("external/MultiPert yok: git clone https://github.com/MengyuanZhaoo/MultiPert external/MultiPert")

    import torch
    torch.set_num_threads(a.threads)
    sys.path.insert(0, str(CODE))
    os.chdir(CODE)  # main.py uses relative imports and paths
    import numpy as np
    import data_loader  # noqa: E402

    # Compatibility shim (behaviour-preserving): the released code indexes a pandas Series with
    # integer positions (perturb_info[idx]). pandas >= 2 no longer falls back to positional access
    # on a string index, so convert it to a numpy array once, as older pandas effectively did.
    _orig_init = data_loader.MultiOmicsDataset.__init__

    def _init(self, rna, adt, perturb_info, *args, **kwargs):
        _orig_init(self, rna, adt, np.asarray(perturb_info), *args, **kwargs)

    data_loader.MultiOmicsDataset.__init__ = _init
    import main as mp  # noqa: E402

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    mp.main(str(CODE.parent / "data"), "PapalexiSatija2021_eccite_arrayed", str(out), a.epochs)
    print(f"[multipert] bitti: {(time.time() - t0) / 60:.1f} dk -> {out}")


if __name__ == "__main__":
    main()
