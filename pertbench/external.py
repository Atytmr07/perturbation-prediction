"""Bridge to external (usually GPU, PyTorch) models: GEARS, CPA, scGen, biolord, CellFlow,
MultiPert, MultiFlow, ...

Those tools have their own environments and data formats, so we do not import
them. Instead:

  1. export_split(...) writes cell-level train/test AnnData for one split, with
     `perturbation`, `cell_type`, `donor`, `split` columns, one file per modality.
  2. You train the external model in its own env and write predicted condition
     means to a CSV:  perturbation, cell_type, donor, modality, <feature_1>, ...
  3. ExternalPredictions(csv) plugs into runner.evaluate_split like any baseline,
     so every model is scored by the same code on the same conditions.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from pertbench.data import KEYS, ConditionTable, PerturbData
from pertbench.models import Model
from pertbench.splits import Split


def export_split(data: PerturbData, ct: ConditionTable, split: Split, outdir: str | Path) -> Path:
    import anndata as ad
    outdir = Path(outdir) / split.name
    outdir.mkdir(parents=True, exist_ok=True)
    test_keys = set(ct.obs.loc[split.test, KEYS].itertuples(index=False, name=None))
    is_test = np.array([k in test_keys for k in data.obs[KEYS].itertuples(index=False, name=None)])
    obs = data.obs.copy()
    obs["split"] = np.where(is_test, "test", "train")
    obs.index = obs.index.astype(str)
    for m, x in data.X.items():
        a = ad.AnnData(X=x, obs=obs, var=pd.DataFrame(index=data.var[m]))
        a.write_h5ad(outdir / f"{m}.h5ad")
    ct.obs.loc[split.test, KEYS].to_csv(outdir / "test_conditions.csv", index=False)
    return outdir


class ExternalPredictions(Model):
    """Replays predictions produced outside pertbench."""

    def __init__(self, csv: str | Path, name: str):
        self.csv, self.name = Path(csv), name

    def _fit(self):
        df = pd.read_csv(self.csv)
        self.table = {}
        for m, g in df.groupby("modality"):
            feats = self.train.var[m]
            vals = g[feats].to_numpy(dtype=float)
            for (p, c, d), v in zip(g[KEYS].itertuples(index=False, name=None), vals):
                self.table[(p, c, d, m)] = v

    def predict(self, query):
        out = {m: [] for m in self.mods}
        for p, c, d in query[KEYS].itertuples(index=False, name=None):
            for m in self.mods:
                v = self.table.get((p, c, d, m))
                out[m].append(v if v is not None else np.full(len(self.train.var[m]), np.nan))
        return {m: np.stack(v) for m, v in out.items()}
