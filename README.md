# perturbation-prediction

Donor-aware multimodal single-cell perturbation response prediction: predict how a **previously unseen donor** responds to a perturbation in several modalities (RNA, ATAC, surface protein), using only that donor's untreated cells. Evaluation is leave-one-donor-out against a `PerturbationMean` baseline.

Results so far: [RESULTS.md](RESULTS.md) · COVID baseline table: [results/LEADERBOARD.md](results/LEADERBOARD.md)

## Layout

| Path | Content |
|---|---|
| `pertbench/` | Benchmark package: pseudobulk condition tables, splits (unseen donor / perturbation / cell type), delta metrics, baselines (`NoChange`, `PerturbationMean`, `Additive`, `ContextKNN`, `ContextRidge`, ...), synthetic multi-donor data |
| `scripts/covid/` | COVID vaccine data (Zhang et al. 2023, Zenodo 7555405): download, inspect and convert Seurat `.rds` without R, LODO baselines |
| `scripts/multipert/` | MultiPert: original run, rescoring, COVID LODO, attention check, variants, unseen-knockout test |
| `scripts/cellflow/` | CellFlow: LODO on synthetic data, seed / setting sweep, aggregation |
| `scripts/run_benchmark.py`, `scripts/download_data.py` | pertbench on public perturbation datasets (scPerturb) |
| `results/` | Summary tables |
| `tests/` | pytest |

External code (`external/MultiPert`, `external/cellflow`) and data (`data/`) are not tracked.

## Setup

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m pip install git+https://github.com/cellgeni/py8rds.git   # read Seurat .rds files
.venv/Scripts/python -m pytest -q tests
```

CellFlow needs Python 3.11 and its own environment:

```bash
git clone https://github.com/theislab/cellflow external/cellflow
uv venv .venv-cellflow --python 3.11
uv pip install --python .venv-cellflow -e external/cellflow requests pytest
```

## Running

```bash
# pertbench baselines
.venv/Scripts/python scripts/run_benchmark.py --dataset synthetic

# COVID: download -> inspect -> convert -> LODO baselines
.venv/Scripts/python scripts/covid/01_download.py
.venv/Scripts/python scripts/covid/04_run_lodo.py --config scripts/covid/config_full.json --strict

# CellFlow LODO on synthetic data; the sweep takes [cores] [hours] and resumes where it stopped
.venv-cellflow/Scripts/python scripts/cellflow/01_synthetic_lodo.py --iterations 50000 --lr 5e-4
bash scripts/cellflow/02_sweep.sh 0 6
.venv-cellflow/Scripts/python scripts/cellflow/03_aggregate.py
```

Rule: the held-out donor never enters preprocessing. Feature selection, scaling and PCA are fit on training donors only.
