"""COVID aşı verisinde leave-one-donor-out baseline'ları: 5 donörle eğit, 6. donörün gün 0'ından
gün 2/10/28 profilini (RNA, ADT, ATAC) tahmin et.

    python scripts/covid/04_run_lodo.py --config scripts/covid/config.json
    python scripts/covid/04_run_lodo.py --config scripts/covid/config.json --strict   # özellik seçimi fold içinde

config.json örneği için scripts/covid/config.example.json'a bakın (sütun adları 02_inspect_rds.py çıktısından).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from pertbench.datasets import covid_vaccine  # noqa: E402
from pertbench.models import default_models  # noqa: E402
from pertbench.runner import evaluate_split, skill_vs_baseline, summarise  # noqa: E402
from pertbench.splits import unseen_context  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--strict", action="store_true", help="feature selection on training donors only (slower)")
    ap.add_argument("--out", default=str(ROOT / "results" / "covid_lodo"))
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    load = lambda train=None: covid_vaccine(train_donors=train, **cfg)  # noqa: E731

    ct = load()
    donors = sorted(ct.obs["donor"].unique())
    print(f"[covid] {len(ct.obs)} koşul | donörler {donors} | modaliteler "
          + ", ".join(f"{m}:{v.shape[1]}" for m, v in ct.means.items()))
    print(ct.obs.groupby(["perturbation"])["n_cells"].describe()[["count", "min", "50%"]])

    frames = []
    for d in donors:
        fold_ct = load([x for x in donors if x != d]) if a.strict else ct
        split = unseen_context(fold_ct, "donor", d)
        for model in default_models(fold_ct.modalities):
            df = evaluate_split(model, fold_ct, split)
            df["split_family"] = "unseen_donor"
            frames.append(df)
        print(f"[covid] fold donör={d} bitti")
    res = pd.concat(frames, ignore_index=True)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res.to_csv(out / "per_condition.csv", index=False)
    summ = summarise(res)
    summ.to_csv(out / "summary.csv", index=False)
    by_day = res.groupby(["modality", "perturbation", "model"])["mse_top20"].mean().unstack("model").round(4)
    by_day.to_csv(out / "mse_top20_by_day.csv")
    skill = skill_vs_baseline(res)
    with pd.option_context("display.width", 220, "display.max_columns", 20):
        print(summ.to_string(index=False))
        print("\nGün bazında top-20 MSE:\n", by_day.to_string())
        print("\nPerturbationMean'e göre skill (>0 daha iyi):\n", skill.to_string())
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
