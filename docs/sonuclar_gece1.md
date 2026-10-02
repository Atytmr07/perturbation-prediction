# Gece 1 Sonuçları (2 Ekim 2026)

## 1. COVID verisi (Zhang vd. 2023)
- İndirildi, MD5 kontrolünden geçti. **R olmadan, `py8rds` ile okunuyor.**
- **CITE:** 113.897 hücre. Assay'ler: RNA (16.825 gen), ADT (175), SCT. Metadata: `donor` (6), `timepoint` (Day0/Day2/**Day11**/Day28; gün 10 değil 11), `celltypel1/2/3` (8/30/47 tip). h5ad'e dönüştürüldü.
- **ASAP:** 78.677 hücre. ATAC: 118.137 peak, ham sayımlar mevcut. **ADT'de sadece `scale.data` var, ham sayım yok.** Hücre tipi etiketleri `predicted.CITE_l1/l2/l3` sütunlarında, yani CITE'tan aktarılmış; adları CITE ile uyumlu. ASAP henüz h5ad'e çevrilmedi. ADT'nin `scale.data` katmanından okunması gerekecek (`03_convert.py --layer scale.data`).

## 2. İlk LODO tablosu (sadece CITE: RNA + ADT, `celltypel1`, `--strict`)
Top-20 MSE (düşük = iyi). Tam tablo: `results/covid_lodo_cite_l1/`.

| Modalite | NoChange | PerturbationMean | ContextKNN | ContextRidge |
|---|---|---|---|---|
| RNA | 0,255 | **0,218** | 0,222 | 0,227 |
| ADT | **0,079** | 0,080 | 0,086 | 0,080 |

- RNA'da en iyi model `PerturbationMean`. Donör-farkında baseline'lar onu **geçemiyor**.
- ADT'de ana hücre tipi düzeyinde aşının etkisi gürültü seviyesinde.

## 3. Donör sinyali var mı? (`scripts/covid/05_signal_noise.py`)
- Gürültü (split-half yöntemiyle tahmin edildi) çıkarıldıktan sonra, cevap farkının **~%40–80'i donöre özgü**. Örnekler: Mono ADT Day2, Day28'de CD8/CD4 T ve Mono.
- **Sonuç:** Tahmin edilecek bir donör sinyali var, ama basit "baseline benzerliği" modelleri onu yakalayamıyor. Model geliştirmenin gerekçesi bu.
- **Uyarı:** Her donör × gün tek bir örnek. Ölçülen donöre özgü farkta örnek düzeyindeki teknik etkiler de olabilir.

## 4. MultiPert, orijinal haliyle (Papalexi arrayed, CPU'da 13 dk, 172. epoch'ta erken durdu)
- **Makale yeniden üretildi.** RNA PCC 0,74–0,80, DEG PCC 0,75–0,91 (makale: 0,78 ve 0,88).
- **Bizim metriklerle** (aynı test hücreleri; `results/multipert_original/rescored_summary.csv`):

| | pearson_delta RNA | mse_top20 RNA | pearson_delta ADT | MMD RNA |
|---|---|---|---|---|
| MultiPert | 0,835 | 0,011 | 0,556 | 1,17 |
| PerturbationMean (aynı perturbation'ın eğitim hücreleri) | **0,861** | **0,007** | **0,953** | ~0 |
| NoChange | – | 0,418 | – | 0,18 |

- **MultiPert, basit "eğitim ortalaması"nı geçemiyor.** Proteinde fark büyük.
- Ürettiği hücrelerin dağılımı gerçek dağılıma çok uzak; MSE ile eğitildiği için çeşitliliği olmayan, ortalamaya yakın hücreler üretiyor.
- Not: MultiPert'in split'inde test perturbation'ları eğitimde de görüldüğü için `PerturbationMean` burada bir "oracle" sayılır. Yine de geçilmesi beklenen bir çıta.

## Sıradaki adımlar
1. ASAP'ı dönüştür: ATAC counts + ADT `scale.data`. Ardından tam multimodal LODO.
2. Hücre tipi düzeyi l2 ile LODO (aşı etkisi alt tiplerde).
3. MultiVI ile entegrasyon. scvi-tools 1.5.1 `.venv-models`'e kuruldu; RNA + ATAC + protein'i, eksik modaliteli hücreler dahil, MuData ile destekliyor. GPU için Kaggle.
