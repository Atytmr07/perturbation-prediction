# MultiPert COVID Donor-Generalization Diagnostics

Bu belge, MultiPert'in COVID aşı CITE-seq verisinde unseen-donor genellemesini test etmek için yapılan tanısal deneyleri özetler. Amaç yalnızca global PCC'ye bakmak değil, modelin gerçekten donor/cell-specific response öğrenip öğrenmediğini ayırt etmektir.

## Veri ve görev

- 6 donor: `donorA`, `donorB`, `donorE`, `donorF`, `donorJ`, `donorM`
- Modaliteler: RNA + ADT
- Day0: control / pretreatment
- Day28: vaccine / treated
- Ana görev: unseen donor için Day0 RNA+ADT kullanarak Day28 RNA+ADT tahmini
- Ana değerlendirme: Leave-One-Donor-Out (LODO)

> Not: Day0 ve Day28 hücreleri aynı fiziksel hücrelerin longitudinal eşleşmeleri değildir. Bu yüzden hücre-düzeyi birebir pairing biyolojik bir ground truth değildir; donor x cell-type pseudobulk ve response-delta analizi daha anlamlıdır.

## 1. Orijinal MultiPert reproduksiyonu

Resmi THP-1 verisinde yaklaşık sonuçlar:

- RNA PCC: **0.78**
- DEG PCC: **0.88**
- Protein PCC: **0.79**

**Yorum:** Resmi implementation başarıyla çalıştırıldı. COVID verisindeki sonraki sorunları yalnızca kurulum/kod hatasıyla açıklamak için güçlü bir neden yok.

## 2. COVID standard cell-level split

Donorlar ayrılmadan hücreler train/validation/test arasında bölündü.

- RNA PCC: **0.692**
- ADT PCC: **0.653**

**Yorum:** Model yeni veri setinde makul global performans gösteriyor; fakat bu split unseen-donor genellemesini test etmiyor.

## 3. Leave-One-Donor-Out

Her fold'da bir donor tamamen testte bırakıldı.

Ortalama:

- RNA PCC: **0.615**
- ADT PCC: **0.631**

**Yorum:** MultiPert unseen donor üzerinde tamamen çökmüyor. Ancak bu değerin kişiselleştirilmiş response öğrenildiğini gösterip göstermediği sonraki baselinelarla test edildi.

## 4. Copy-control baseline

Baseline: `Day28 prediction = Day0 input`.

LODO ortalaması:

- RNA: Copy-control **0.408** vs MultiPert **0.615**
- ADT: Copy-control **0.488** vs MultiPert **0.631**

MultiPert 6/6 donorda copy-control'den daha iyiydi.

**Yorum:** Model yalnızca Day0 profilini kopyalamıyor.

## 5. Mean-Day28 baseline

Training donorlarının ortalama Day28 profili herkese prediction olarak verildi.

- RNA: Mean-Day28 **0.616** vs MultiPert **0.615**
- ADT: Mean-Day28 **0.633** vs MultiPert **0.631**

**Yorum:** Kişiselleştirme yapmayan population-average baseline MultiPert ile aynı seviyede. Bu nedenle yüksek flattened/global PCC, donor-specific prediction kanıtı değildir.

## 6. Cell-type pseudobulk ve response delta

Response tanımı:

`Delta = Day28 - Day0`

Donor x cell-type pseudobulk düzeyinde:

- RNA Delta PCC: MultiPert **0.193** vs Mean-Day28 **0.233**
- ADT Delta PCC: MultiPert **0.150** vs Mean-Day28 **0.152**

**Yorum:** Model genel treated state'i yakalayabilse de donor-specific vaccine-induced change zayıf tahmin ediliyor.

## 7. Same-donor + same-cell-type control matching

İlk LODO'da control aynı donordan seçiliyor fakat aynı cell type zorunlu değildi. Pairing şu şekilde düzeltildi:

`same donor + same cell type`

Örnek donorM RNA PCC:

- Önce: **0.5994**
- Cell-type matched: **0.5998**

DonorJ RNA PCC:

- Önce: **0.6107**
- Cell-type matched: **0.6079**

**Yorum:** Cell-type matching global performansı anlamlı biçimde değiştirmedi. Sorunun ana nedeni yalnızca yanlış control-cell eşleşmesi değil.

## 8. Cell-type-specific Mean-Delta baseline

Her cell type için training donorlarında ortalama response hesaplandı:

`mean_delta_ct = mean_donors(Day28_ct - Day0_ct)`

Unseen donor prediction:

`Predicted Day28 = Held-out donor Day0 + mean_delta_ct`

### Absolute Day28

RNA:

- MultiPert PCC: **0.884**
- Mean-Delta PCC: **0.986**
- MultiPert MSE: **0.077**
- Mean-Delta MSE: **0.007**

ADT:

- MultiPert PCC: **0.795**
- Mean-Delta PCC: **0.993**
- MultiPert MSE: **0.664**
- Mean-Delta MSE: **0.026**

### Response Delta

- RNA: MultiPert **0.194** vs Mean-Delta **0.190**
- ADT: MultiPert **0.150** vs Mean-Delta **0.103**

**Yorum:** Basit `Day0 + mean response` yaklaşımı donorun pretreatment state'ini çok daha iyi koruyor. MultiPert delta tarafında açık ve tutarlı bir üstünlük göstermiyor.

## 9. Prediction variance / collapse analizi

Gerçek Day28 hücreleri ile prediction hücreleri arasındaki feature-wise varyans karşılaştırıldı.

Ortalama:

- RNA true mean variance: **2.856e-1**
- RNA predicted mean variance: **1.096e-10**
- RNA variance ratio: **3.84e-10**
- ADT true mean variance: **1.449**
- ADT predicted mean variance: **1.043e-8**
- ADT variance ratio: **7.42e-9**

DonorM sanity check:

- 5054 RNA prediction, 5 ondalığa yuvarlayınca yalnız **3** unique row
- 5054 ADT prediction, 5 ondalığa yuvarlayınca yalnız **5** unique row
- Predicted cell0 vs cell1 max fark: **0**
- Predicted cell0 vs cell100 max fark: **0**

**Yorum:** Tahminler hücreler arasında pratik olarak değişmiyor; model common treated-state profile'a collapse ediyor.

## 10. Prediction permutation testi

Prediction satırları rastgele hücrelere karıştırıldı. Hücreye özgü bilgi taşıyan bir modelde performansın düşmesi beklenir.

Ortalama:

- RNA original PCC: **0.614740**
- RNA shuffled PCC: **0.614740**
- RNA PCC drop: **2.15e-12**
- ADT original PCC: **0.631402**
- ADT shuffled PCC: **0.631402**
- ADT PCC drop: **2.43e-11**

MSE de pratik olarak değişmedi.

**Yorum:** Hangi predicted row'un hangi gerçek hücreyle eşleştiğinin önemi yok. Bu sonuç prediction-collapse bulgusunu doğrudan destekliyor.

# Temel sonuç

MultiPert'in bu COVID-vaccine adaptasyonunda:

1. Model genel Day28/treatment state'i öğrenebiliyor.
2. Unseen donor üzerinde copy-control'den daha iyi global PCC üretiyor.
3. Ancak basit Mean-Day28 population baseline'ını anlamlı biçimde geçemiyor.
4. Donor-specific `Day28-Day0` response delta tahmini zayıf.
5. Same-donor + same-cell-type pairing bu problemi çözmüyor.
6. `Day0 + cell-type mean response` baseline'ı absolute Day28 state'i MultiPert'ten çok daha iyi koruyor.
7. Prediction varyansı pratik olarak sıfır.
8. Prediction satırlarını karıştırmak PCC/MSE'yi değiştirmiyor.
9. Bu nedenle mevcut adaptasyon cell-specific veya donor-specific prediction üretmek yerine common population-level treated profile'a collapse ediyor.
10. Sonraki modelin hedefi, unseen donorun pretreatment RNA+ADT state'ini koruyup donor-specific response delta'yı tahmin etmek olmalı.

## Tekrar çalıştırılabilir tanısal scriptler

- `scripts/multipert/04_covid_prediction_collapse.py`
  - variance ratio
  - unique predicted rows
  - prediction permutation sensitivity

- `scripts/multipert/05_covid_celltype_baselines.py`
  - donor x cell-type pseudobulk
  - Mean-Day28 baseline
  - cell-type Mean-Delta baseline
  - absolute Day28 ve response-delta metrikleri

Ham `.h5ad` dosyaları, model checkpointleri ve büyük ara çıktılar repoya eklenmemelidir.
