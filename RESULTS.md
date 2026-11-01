# Results

Question: can we predict a **multimodal** perturbation response in a **completely unseen donor** from that donor's untreated cells? All evaluations are leave-one-donor-out (or leave-one-perturbation-out where stated), use delta metrics on pseudobulk means, and compare against `PerturbationMean` (the mean change of the training donors / perturbations).

Metrics: `pearson_delta` (correlation of predicted vs true change, higher is better), `mse_top20` (error on the 20 most changed features, lower is better), and MMD / energy distance between predicted and true cells (lower is better).

## 1. Baselines on COVID vaccine data

See [results/LEADERBOARD.md](results/LEADERBOARD.md). On 6 donors the vaccine effect is small; no donor-aware baseline (ContextRidge, ContextKNN) clearly beats `PerturbationMean`.

## 2. MultiPert (Zhao et al. 2026)

- **Predictions do not depend on the input cell.** In `DualFusionAttention` the cross-attention gets a sequence of length 1, so the softmax weight is always 1 and the output is a function of the perturbation only; there is no residual path. Different cells with the same perturbation give identical outputs (`scripts/multipert/06_attention_check.py`). This matches the equations in the paper, so it is a design property, not a code bug.
- **COVID (LODO, RNA + protein):** predictions collapse to one profile per day; top-20 MSE is 3–4× `PerturbationMean` (table in the leaderboard). An independent pipeline (`scripts/multipert/04–05`) found the same collapse.
- **Variants on THP-1** (`scripts/multipert/07_variants.py`): residual / FiLM conditioning lets the cell reach the output; a group-level MMD + mean loss restores realistic cell spread (MMD 1.18 → 0.06). No variant beats `PerturbationMean` on that split, because test knockouts are also in training.
- **Unseen knockout** (`scripts/multipert/09_unseen_knockout.py`, leave-one-knockout-out, 9 knockouts): MultiPert does not beat "control + mean effect of the other knockouts".

| Model | RNA pearson_δ | RNA mse_top20 | Protein pearson_δ | Protein mse_top20 |
|---|---|---|---|---|
| LeaveOutMean | **0.688** | **0.243** | **0.460** | **0.004** |
| MultiPert, shipped embeddings | 0.564 | 0.272 | 0.448 | 0.067 |
| MultiPert, leakage-free GEARS embeddings | 0.583 | 0.265 | 0.387 | 0.099 |
| MultiPert FiLM + MMD/mean loss | 0.468 | 0.291 | 0.142 | 0.013 |

## 3. CellFlow (Klein et al. 2025) on synthetic multi-donor data

CellFlow is a flow-matching model that represents each donor by the mean of its control cells and starts each prediction from that donor's own controls. The paper evaluates fully unseen donors, but only on RNA. Here it runs on synthetic data with RNA, ATAC and protein measured in the same cells (`pertbench.make_synthetic`), in a joint PCA space (30 PCs, fit on training donors only).

- Scripts: `scripts/cellflow/01_synthetic_lodo.py` (one LODO run), `02_sweep.sh` (settings × seeds), `03_aggregate.py`.
- Output: `results/cellflow_sweep/aggregate.csv`.
- Settings:
  - Linear or nonlinear donor effect. With `donor_nonlinear=0.5`, donor sensitivity gets a quadratic term that is not linear in the control profile.
  - Large (8 donors, 30 perturbations) or small (6 donors, 3 perturbations, COVID-like).
- Training: 50k iterations, lr 5e-4, ~10 min per fold on CPU.

**RNA.** Top-20 MSE columns are the median over donor folds of the per-fold ratio CellFlow / baseline; below 1 means CellFlow is better.

| Setting | Seeds | pearson_δ PerturbationMean / ContextRidge / CellFlow | mse_top20 CellFlow ÷ PerturbationMean | mse_top20 CellFlow ÷ ContextRidge |
|---|---|---|---|---|
| Linear, 8 donors, 30 perts | 1 | 0.86 / **0.89** / 0.81 | **0.46** | 0.88 |
| Nonlinear, 8 donors, 30 perts | 3 | 0.74 / **0.79** / 0.70 | **0.61** | 1.11 |
| Linear, 6 donors, 3 perts | 3 | 0.83 / **0.85** / 0.74 | 1.00 | 1.04 |
| Nonlinear, 6 donors, 3 perts | 3 | 0.76 / **0.79** / 0.66 | 1.00 | 1.16 |

Findings:
1. **Overall delta correlation.** The ranking is ContextRidge > `PerturbationMean` > CellFlow in every setting and seed. CellFlow is noisy on features that change little.
2. **Most-changed features.** CellFlow roughly halves the error of `PerturbationMean` only when there are many perturbations. In the small setting there is no gain.
3. **Against ContextRidge.** CellFlow is on par with ContextRidge per fold, with median ratios 0.9–1.2. Its mean-level advantage in single runs comes from large gains on a few outlier donors.
4. **Nonlinear donor effects** do not shift the comparison towards CellFlow.
5. **ATAC and protein.** In the small nonlinear setting, CellFlow has the best ATAC and protein delta correlation (0.66 and 0.64, against 0.63 and 0.59 for ContextRidge). In the large nonlinear setting, ContextRidge is better on protein.
6. **Cell distributions.** CellFlow is the only model here that predicts them (energy distance 1.5 vs 4.2 for NoChange in the small nonlinear setting, seed 0).

Takeaway:
- On data the size of the COVID set, CellFlow should not be expected to beat a donor-aware linear baseline on mean profiles. ContextRidge has to be reported next to it.
- CellFlow is still the most suitable base model for this project: it is the only one that is donor-aware and predicts cell distributions.

## Limitations

- Synthetic data only for CellFlow; the three modalities are measured in the same cells there. In the real data (CITE-seq vs ASAP-seq) they are not. The next step is to replace the PCA space with a multimodal integration latent (MultiVI / MIDAS, with assay, not donor, as batch).
- Hyperparameters were chosen on one fold of one setting.
