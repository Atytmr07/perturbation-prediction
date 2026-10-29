# CellFlow: kurulum ve sentetik veride ilk LODO denemesi

*Script: `scripts/cellflow/01_synthetic_lodo.py` · sonuçlar: `results/cellflow_synthetic_lodo/` · log: `results/cellflow_synthetic_lodo.log`*

## Makaleden kontrol edilenler
Kaynak: Klein vd. 2025, bioRxiv 10.1101/2025.04.11.648220 (`docs/papers/Klein2025_CellFlow_bioRxiv.pdf`).

- **Tamamen görülmemiş donör test edilmiş.**
  - Methods'ta "i = 0" modeli var: test donörünün eğitimde hiçbir sitokin cevabı yok, sadece kontrol hücreleri var.
  - Şekil 2F'den gözle okunan sonuç: CellFlow DEG R² ~0,80. Baseline'lar: "bu sitokinin diğer donörlerdeki ortalaması" ~0,68, hiç değişmez ~0,70. Enerji uzaklığı CellFlow ~25, baseline'lar ≥50.
- **Donör temsili:** Kontrol hücrelerinin ortalama ifade vektörü. Makalede: "we computed the donor-specific mean gene expression vector of the control population".
- **Dikkat edilmesi gerekenler:**
  - Veri 12 donör × 90 sitokin; diğer donörlerde her sitokin ölçülmüş.
  - R² ham ortalamalar üzerinden hesaplanıyor; hiç değişmez modeli bile ~0,70 alıyor.
  - Değerlendirme PCA'sı test verisi dahil tüm veriyle hesaplanmış.

## Kurulum
- **Ortam:** `.venv-cellflow`, Python 3.11 (`uv venv --python 3.11`). `pip install -e external/cellflow requests`.
- **Kütüphaneler:** JAX 0.10.2 (CPU), ott-jax 0.6.0. CellFlow'un `scikit-learn==1.5.1` sabitlemesi yüzünden Python 3.13 yerine 3.11 kullanıldı.
- **CellFlow'un kendi testleri:** `tests/model` 15 dakikalık süre sınırına kadar hatasız geçti; o sürede bitmedi.
- **Not:** CellFlow, eğitim verisinde hedef dağılımı olmayan bir kontrol grubuna izin vermiyor. Bu yüzden test donörünün kontrol hücreleri eğitime girmiyor, sadece tahmin aşamasında başlangıç hücreleri olarak kullanılıyor.

## Deney
- **Veri:** `make_synthetic(n_donors=8)`; 3 hücre tipi, 30 perturbation, RNA + protein + ATAC.
  - Donör etkisi doğrusal: donör, temel ifadeyi kaydırıyor ve program hassasiyetini değiştiriyor.
- **LODO:** Her donör sırayla test donörü; o donörün bütün perturbe hücreleri gizli.
- **Hücre uzayı:**
  - Üç modalite z-skorlanıp birleştiriliyor ve 30 PC'ye indiriliyor.
  - Ölçekleme ve PCA sadece eğitim donörlerinden hesaplanıyor.
  - Tahminler geri çevrilip her modalitede ayrı ayrı skorlanıyor.
- **CellFlow:**
  - Bağlam (donör × hücre tipi) temsili = o bağlamın kontrol hücrelerinin PCA ortalaması. Perturbation temsili = one-hot.
  - Ayarlar: katman genişliği 256, 50 bin iterasyon, batch 256, Adam 5e-4. CPU'da donör başına ~10 dakika.
  - Ayar seçimi sadece donor0 üzerinde yapıldı:
    - 500 iterasyonda model bir şey öğrenmemişti.
    - 20 bin iterasyonda 5e-4, 1e-4'ten iyiydi.
    - 50 bin iterasyonda 30 PC, 60 PC'den iyiydi.
- **PCAOracle:** Gerçek test hücreleri PCA'dan geçip geri çevrilince elde edilen skor. Bu uzaydaki herhangi bir model için ulaşılabilecek tavan.

## Sonuçlar (8 donör, bütün test koşullarının ortalaması)

| Model | RNA delta PCC | RNA top-20 MSE | ATAC delta PCC | ATAC top-20 MSE | Protein delta PCC | Protein top-20 MSE | Enerji uzaklığı (PCA) |
|---|---|---|---|---|---|---|---|
| NoChange | – | 8,61 | – | 3,54 | – | 1,77 | 9,77 |
| PerturbationMean | 0,863 | 2,14 | 0,816 | 1,04 | 0,848 | 0,41 | – |
| ContextRidge | **0,890** | 1,35 | **0,846** | 0,67 | **0,862** | **0,27** | – |
| **CellFlow** | 0,809 | **1,00** | 0,811 | **0,47** | 0,778 | 0,30 | **2,12** |
| PCAOracle | 0,946 | 0,08 | 0,976 | 0,01 | 0,900 | 0,10 | – |

**Donör başına top-20 MSE, 8 donörün medyanı:**

| | PerturbationMean | ContextRidge | CellFlow |
|---|---|---|---|
| RNA | 0,95 | 0,42 | **0,38** |
| ATAC | 0,40 | 0,19 | **0,15** |
| Protein | 0,21 | **0,14** | 0,23 |

## Yorum
1. **CellFlow, en çok değişen genlerde `PerturbationMean`'i açıkça geçiyor.**
   - RNA top-20 MSE: 1,00'a karşı 2,14. ATAC: 0,47'ye karşı 1,04.
   - Yani görülmemiş donörün kendine özgü cevabını kısmen yakalıyor. MultiPert bunu yapamıyordu (bkz. `docs/15`, `docs/17`).
   - Bu kazanç en çok diğerlerinden farklı donörlerde görülüyor: donor7, donor2, donor3. Örneğin donor7'de RNA top-20 MSE: CellFlow 4,9; ContextRidge 7,4; PerturbationMean 10,4.
2. **Genel delta PCC'de en kötü model CellFlow.**
   - RNA'da 0,81'e karşı 0,86–0,89.
   - Büyük değişimleri iyi yakalıyor, ama küçük değişimli özelliklerde gürültülü. Bunun sebebi her hücrenin ayrı ayrı akıtılması ve ortalamanın sonlu sayıda hücreden alınması olabilir.
3. **Proteinde ContextRidge daha iyi.**
   - Protein, birleştirilmiş uzayda 330 özelliğin sadece 30'u.
   - Proteine özgü etkiler PCA'da zayıf temsil ediliyor olabilir. PCAOracle'ın protein tavanı da daha düşük: 0,90.
4. **Dağılımı yalnızca CellFlow tahmin ediyor.** Enerji uzaklığı 9,8'den 2,1'e iniyor. Diğer modeller sadece ortalama veriyor.
5. **Sentetik veride donör etkisi doğrusal olduğu için ContextRidge'in burada avantajlı olması beklenir.** Gerçek veride bu sıralama değişebilir.

## Sınırlılıklar ve sonraki adımlar
- **Tek seed ve tek sentetik veri.** Ayarlar donor0 üzerinde seçildi; tam ayar taraması yapılmadı.
- **Bu deneme multimodal entegrasyon değil.** Sentetik veride üç modalite aynı hücrelerde ölçülüyor. Gerçek veride modaliteler farklı hücrelerde ölçüldüğü için önce bir entegrasyon latent'i (MultiVI / MIDAS) gerekecek. Bu latent, buradaki PCA'nın yerine geçecek.
- **Sonraki adımlar:**
  - Daha uzun eğitim veya modaliteye göre ağırlıklandırılmış PCA.
  - Birkaç seed ile tekrar.
  - Ardından gerçek veriye geçmek.
