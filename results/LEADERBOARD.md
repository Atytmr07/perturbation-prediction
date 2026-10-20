# Leaderboard: COVID aşı verisi, leave-one-donor-out

Ortak protokol: `docs/12_roadmap_ekim_sonu.md`. Değerlendirme: 6 fold, `--strict` (özellik seçimi her fold'da sadece eğitim donörlerinden). Değerler tüm test koşullarının (gün × hücre tipi) ortalaması.
- `pearson_delta`: yüksek = iyi.
- `mse_top20`: en çok değişen 20 özellikteki hata; düşük = iyi.

**Çıta: `PerturbationMean`.**

## Tam multimodal: CITE (RNA + protein) + ASAP (ATAC + protein), hücre tipi l1 (8 tip)
*7 Ekim 2026 · `results/covid_lodo_full_l1/` · 176 koşul (iki assay'de de ≥10 hücre olanlar), 128 test koşulu. Kontrolsüz 9 koşul atlandı.*

| Model | İz | RNA pearson_δ | RNA mse_top20 | CITE-protein pearson_δ | CITE-protein mse_top20 | ATAC pearson_δ | ATAC mse_top20 | ASAP-protein pearson_δ | ASAP-protein mse_top20 | Not |
|---|---|---|---|---|---|---|---|---|---|---|
| NoChange | 0 | – | 0,203 | – | 0,059 | – | 0,071 | – | 0,033 | Değişim yok |
| **PerturbationMean** | 0 | 0,278 | **0,165** | **0,103** | 0,059 | 0,020 | 0,071 | 0,107 | 0,031 | **Çıta** |
| Additive | 0 | 0,272 | 0,168 | 0,087 | **0,058** | 0,016 | 0,071 | 0,110 | 0,031 | |
| ContextKNN | 0 | 0,226 | 0,178 | 0,023 | 0,065 | 0,019 | 0,071 | 0,089 | 0,032 | Donör-farkında |
| ContextRidge | 0 | **0,287** | 0,174 | 0,077 | 0,059 | 0,021 | **0,070** | 0,109 | 0,031 | Donör-farkında |
| CrossModal[PerturbationMean] | 0 | 0,278 | 0,165 | 0,090 | 0,058 | **0,024** | 0,070 | **0,121** | **0,030** | Protein/ATAC'ı RNA değişiminden tahmin ediyor |

## Tam multimodal, ince hücre tipi l2 (CITE `celltypel2` / ASAP `predicted.CITE_l2`)
*12 Ekim 2026 · `results/covid_lodo_full_l2/` · 384 koşul, 263 test koşulu. Kontrolsüz koşullar atlandı.*

| Model | RNA pearson_δ | RNA mse_top20 | CITE-protein pearson_δ | CITE-protein mse_top20 | ATAC pearson_δ | ATAC mse_top20 | ASAP-protein pearson_δ | ASAP-protein mse_top20 |
|---|---|---|---|---|---|---|---|---|
| NoChange | – | 0,240 | – | **0,068** | – | **0,107** | – | **0,040** |
| **PerturbationMean** | 0,211 | **0,205** | **0,071** | 0,070 | 0,011 | 0,109 | 0,054 | 0,042 |
| Additive | 0,211 | 0,208 | 0,067 | 0,069 | 0,010 | 0,109 | 0,053 | 0,042 |
| ContextKNN | 0,187 | 0,214 | 0,011 | 0,076 | 0,010 | 0,109 | 0,045 | 0,043 |
| ContextRidge | **0,231** | 0,215 | 0,017 | 0,071 | 0,012 | 0,107 | 0,039 | 0,040 |
| CrossModal[PerturbationMean] | 0,211 | 0,205 | 0,066 | 0,069 | 0,012 | 0,108 | **0,057** | 0,041 |

ContextRidge, RNA'da test koşullarının sadece %35'inde PerturbationMean'den iyi.

## Sadece CITE (RNA + protein), hücre tipi l1
*2 Ekim 2026 · `results/covid_lodo_cite_l1/` · 192 koşul. Koşul kümesi tam tablodan farklı olduğu için sayılar doğrudan karşılaştırılamaz.*

| Model | RNA pearson_δ | RNA mse_top20 | Protein pearson_δ | Protein mse_top20 |
|---|---|---|---|---|
| NoChange | – | 0,255 | – | 0,079 |
| **PerturbationMean** | 0,250 | **0,218** | **0,096** | 0,080 |
| Additive | 0,240 | 0,222 | 0,081 | 0,079 |
| ContextKNN | 0,224 | 0,222 | 0,015 | 0,086 |
| ContextRidge | 0,224 | 0,227 | 0,049 | 0,080 |

## MultiPert (iz A): CITE (RNA + protein), hücre tipi l1
*20 Ekim 2026 · `scripts/multipert/03_covid_lodo.py` · `results/multipert_covid_{donor,random}_celltypel1_s1/` · 144 test koşulu (3 gün × hücre tipi × donör).*
*Farklı ön işleme uzayı: her fold'da eğitim donörlerinden 2.000 HVG, RNA ve protein CP10k + log1p, hücre sınırı 300 / donör × gün × tip. Baseline'lar aynı uzayda yeniden hesaplandı; bu yüzden üstteki tablolarla doğrudan karşılaştırılamaz.*

| Model | RNA pearson_δ | RNA mse_top20 | Protein pearson_δ | Protein mse_top20 | Not |
|---|---|---|---|---|---|
| NoChange | – | 0,201 | – | **0,183** | |
| **PerturbationMean** | 0,283 | **0,170** | 0,066 | 0,192 | **Çıta** |
| Additive | 0,260 | 0,173 | 0,054 | 0,190 | |
| ContextRidge | **0,285** | 0,173 | 0,071 | **0,183** | |
| MultiPert[donor] | 0,180 | 0,595 | 0,154 | 0,807 | Gün 0 partneri aynı donör ve hücre tipinden |
| MultiPert[random] | 0,182 | 0,597 | **0,155** | 0,805 | Orijinal rastgele eşleşme |

Tahminler hücreler arasında sabit (tahmin std ≈ 0, gerçek 0,19). Ayrıntı: `docs/14_multipert_covid_sonuclar.md`, Bengisu'nun bağımsız tanı analizi `docs/13_multipert_covid_diagnostics.md`.
