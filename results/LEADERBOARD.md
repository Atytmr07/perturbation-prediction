# Leaderboard: COVID aşı verisi, leave-one-donor-out

Ortak protokol: `docs/11_ortak_roadmap.md`. Metrikler, 6 fold ve tüm (gün × hücre tipi) koşulları üzerinden ortalama.
- `pearson_delta`: yüksek = iyi.
- `mse_top20`: en çok değişen 20 özellikte hata; düşük = iyi.

**Çıta: `PerturbationMean`.**

| Model | İz | Veri / modalite | Hücre tipi | Seed | RNA pearson_delta | RNA mse_top20 | Protein pearson_delta | Protein mse_top20 | ATAC mse_top20 | Not |
|---|---|---|---|---|---|---|---|---|---|---|
| NoChange | 0 | CITE (RNA + protein) | l1 (8) | – | – | 0,255 | – | 0,079 | – | Değişim yok |
| PerturbationMean | 0 | CITE | l1 | – | 0,250 | 0,218 | 0,096 | 0,080 | – | **Çıta** |
| Additive | 0 | CITE | l1 | – | 0,240 | 0,222 | 0,081 | 0,079 | – | |
| ContextKNN | 0 | CITE | l1 | – | 0,224 | 0,222 | 0,015 | 0,086 | – | Donör-farkında |
| ContextRidge | 0 | CITE | l1 | – | 0,224 | 0,227 | 0,049 | 0,080 | – | Donör-farkında |

*Kaynak: `results/covid_lodo_cite_l1/` (2 Ekim, `--strict`). ATAC sütunu, ASAP dönüşümünden sonra doldurulacak.*
