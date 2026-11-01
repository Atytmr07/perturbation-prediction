# Leaderboard: COVID vaccine data, leave-one-donor-out

Data: Zhang et al. 2023 (Nat Immunol), 6 donors, days 0 / 2 / 11 / 28; CITE-seq (RNA + protein) and ASAP-seq (ATAC + protein) on different cells. Task: predict each held-out donor's day 2/11/28 pseudobulk profile from its day-0 cells.

Protocol: 6 folds, `--strict` (feature selection on the training donors of each fold only). Values are means over all test conditions (day × cell type).
- `pearson_delta`: higher is better.
- `mse_top20`: error on the 20 most changed features; lower is better.

**Bar to beat: `PerturbationMean`** (the mean change of the training donors).

## Full multimodal: CITE (RNA + protein) + ASAP (ATAC + protein), cell type l1 (8 types)
*`results/covid_lodo_full_l1/` · 176 conditions (≥10 cells in both assays), 128 test conditions; 9 conditions without a control group skipped.*

| Model | RNA pearson_δ | RNA mse_top20 | CITE-protein pearson_δ | CITE-protein mse_top20 | ATAC pearson_δ | ATAC mse_top20 | ASAP-protein pearson_δ | ASAP-protein mse_top20 | Note |
|---|---|---|---|---|---|---|---|---|---|
| NoChange | – | 0.203 | – | 0.059 | – | 0.071 | – | 0.033 | No change |
| **PerturbationMean** | 0.278 | **0.165** | **0.103** | 0.059 | 0.020 | 0.071 | 0.107 | 0.031 | **Bar** |
| Additive | 0.272 | 0.168 | 0.087 | **0.058** | 0.016 | 0.071 | 0.110 | 0.031 | |
| ContextKNN | 0.226 | 0.178 | 0.023 | 0.065 | 0.019 | 0.071 | 0.089 | 0.032 | Donor-aware |
| ContextRidge | **0.287** | 0.174 | 0.077 | 0.059 | 0.021 | **0.070** | 0.109 | 0.031 | Donor-aware |
| CrossModal[PerturbationMean] | 0.278 | 0.165 | 0.090 | 0.058 | **0.024** | 0.070 | **0.121** | **0.030** | Protein/ATAC change predicted from the RNA change |

## Full multimodal, fine cell type l2 (CITE `celltypel2` / ASAP `predicted.CITE_l2`)
*`results/covid_lodo_full_l2/` · 384 conditions, 263 test conditions.*

| Model | RNA pearson_δ | RNA mse_top20 | CITE-protein pearson_δ | CITE-protein mse_top20 | ATAC pearson_δ | ATAC mse_top20 | ASAP-protein pearson_δ | ASAP-protein mse_top20 |
|---|---|---|---|---|---|---|---|---|
| NoChange | – | 0.240 | – | **0.068** | – | **0.107** | – | **0.040** |
| **PerturbationMean** | 0.211 | **0.205** | **0.071** | 0.070 | 0.011 | 0.109 | 0.054 | 0.042 |
| Additive | 0.211 | 0.208 | 0.067 | 0.069 | 0.010 | 0.109 | 0.053 | 0.042 |
| ContextKNN | 0.187 | 0.214 | 0.011 | 0.076 | 0.010 | 0.109 | 0.045 | 0.043 |
| ContextRidge | **0.231** | 0.215 | 0.017 | 0.071 | 0.012 | 0.107 | 0.039 | 0.040 |
| CrossModal[PerturbationMean] | 0.211 | 0.205 | 0.066 | 0.069 | 0.012 | 0.108 | **0.057** | 0.041 |

ContextRidge beats PerturbationMean on RNA in only 35% of test conditions.

## CITE only (RNA + protein), cell type l1
*`results/covid_lodo_cite_l1/` · 192 conditions. Different condition set, so not directly comparable with the tables above.*

| Model | RNA pearson_δ | RNA mse_top20 | Protein pearson_δ | Protein mse_top20 |
|---|---|---|---|---|
| NoChange | – | 0.255 | – | 0.079 |
| **PerturbationMean** | 0.250 | **0.218** | **0.096** | 0.080 |
| Additive | 0.240 | 0.222 | 0.081 | 0.079 |
| ContextKNN | 0.224 | 0.222 | 0.015 | 0.086 |
| ContextRidge | 0.224 | 0.227 | 0.049 | 0.080 |

## MultiPert: CITE (RNA + protein), cell type l1
*`scripts/multipert/03_covid_lodo.py` · `results/multipert_covid_{donor,random}_celltypel1_s1/` · 144 test conditions (3 days × cell type × donor).*
*Different preprocessing: per fold 2,000 HVGs from the training donors, RNA and protein CP10k + log1p, at most 300 cells per donor × day × type. Baselines were recomputed in the same space, so the numbers are not comparable with the tables above.*

| Model | RNA pearson_δ | RNA mse_top20 | Protein pearson_δ | Protein mse_top20 | Note |
|---|---|---|---|---|---|
| NoChange | – | 0.201 | – | **0.183** | |
| **PerturbationMean** | 0.283 | **0.170** | 0.066 | 0.192 | **Bar** |
| Additive | 0.260 | 0.173 | 0.054 | 0.190 | |
| ContextRidge | **0.285** | 0.173 | 0.071 | **0.183** | |
| MultiPert[donor] | 0.180 | 0.595 | 0.154 | 0.807 | Day-0 partner from the same donor and cell type |
| MultiPert[random] | 0.182 | 0.597 | **0.155** | 0.805 | Original random pairing |

MultiPert's predictions are constant across cells (prediction sd ≈ 0, true 0.19); see [RESULTS.md](../RESULTS.md).
