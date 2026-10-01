# Donör Bazlı Multimodal Tahmin: MultiPert Üzerinden Plan

*2 Ekim 2026. Hocanın yönlendirmesine göre güncellendi: odak donör değişimi; MultiFlow şimdilik kapsam dışı.*

## 1. Problem tanımı

10 donörün hücreleri aynı perturbation'lara (ör. LPS, anti-CD3/CD28) maruz bırakılmış. Her hücrede RNA ve yüzey proteinleri (CITE-seq) ölçülmüş.

**Görev:**
- 9 donörün tüm verisiyle (kontrol + perturbe) modeli eğit.
- 10. donör için elimizde sadece kontrol hücreleri var. Bu donörün perturbe hücrelerinin RNA **ve** protein profillerini tahmin et.
- Her donör sırayla test donörü olur: **leave-one-donor-out**, 10 fold.

**Asıl soru:** Model, yeni donörün cevabını "9 donörün ortalama cevabı"ndan daha iyi tahmin edebiliyor mu? Bu ortalama bizim `PerturbationMean` baseline'ımız.
- Edebiliyorsa, donöre özgü bilgiyi (kontrol profili, genotip) kullanabiliyor demektir.
- Edemiyorsa, ya donörler arası cevap farkı küçük, ya da model bu farkı yakalayamıyor. Bu ikisini ayırmak da çalışmanın bir parçası.

## 2. Veri: çok donörlü ve multimodal perturbation

| Veri | Donör | Perturbation | Modalite | Hücre | Uygunluk |
|---|---|---|---|---|---|
| **Lawlor vd. 2021, Front Immunol** (JAX) | **10** (5K/5E, 21–32 yaş) | Kontrol, anti-CD3/CD28 (24 sa), LPS (24 sa) | RNA + **39 protein** (CITE-seq) | ~16 bin (donör×koşul başına ~550) | **Birebir uyuyor.** Her donörde 3 koşul var. Donör **genotipleri** de paylaşılmış (VCF) |
| OP3 / NeurIPS 2023 | 3 | 146 ilaç | Perturbe örneklerde sadece RNA (ATAC yalnızca baseline'da) | büyük | Donör az, multimodal değil |
| Parse 10M PBMC | 12 | 90 sitokin | Sadece RNA | 9,7 M | Donör ekseni için güçlü, ama multimodal değil. RNA tarafında kontrol deneyi olarak kullanılabilir |
| Kang 2018 | 8 | IFN-β | Sadece RNA | ~25 bin | Klasik RNA-only donör benchmark'ı |
| Aquino 2023, Nature | 222 | IAV, SARS-CoV-2 | RNA (CITE-seq durumu doğrulanmalı) | ~1 M | Donör sayısı çok büyük. Protein ölçümü varsa ideal |

**Lawlor 2021'in erişim durumu:**
- ENA'da ham FASTQ var (PRJEB40376, havuzlanmış kütüphaneler).
- Donör genotipleri var (ERZ1631464, `tcell_monocytes_vars.vcf.gz`).
- Hazır işlenmiş count matrisi bulamadık. İnteraktif portal: https://czi-pbmc-cite-seq.jax.org/

İki yol var:
- (a) Yazarlardan veya portaldan işlenmiş matrisi istemek. **Önerilen yol.**
- (b) FASTQ'dan CellRanger + hashtag/genotip ile demultiplex (demuxlet/vireo) yapmak. Küme gerekir.

**Riskler:**
- Hücre sayısı küçük. Donör × koşul × hücre tipi kırılımında bazı gruplar 20–50 hücreye düşer.
- Sadece 2 perturbation var. Bu yüzden "görülmemiş perturbation" görevi bu veride yapılamaz. Bizim için sorun değil, çünkü eksen donör.

## 3. MultiPert'in kodundan çıkanlar

Repo: https://github.com/MengyuanZhaoo/MultiPert. Kodun tamamı yaklaşık 900 satır.

| Konu | Koddaki durum | Donör kurgusu için sonucu |
|---|---|---|
| Veri | Repo Papalexi 2021 "arrayed" ECCITE-seq ile geliyor (THP-1, tek hücre hattı) | Donör ekseni yok |
| Kontrol–perturbe eşleşmesi | Her perturbe hücreye **rastgele** bir kontrol hücresi atanıyor (`sample_data`), tüm kontrol havuzundan | Donörler karışıyor. **Eşleşme aynı donör (ve aynı hücre tipi) içinden yapılmalı** |
| Train/test ayrımı | Her perturbation'ın hücreleri 60/20/20 oranında bölünüyor (`split_dataset`) | Testteki her perturbation eğitimde de var; görev interpolasyon. **Donör bazlı bölünmeli** |
| Perturbation temsili | GEARS GO embedding'i (64 boyut). Gen değilse one-hot | LPS ve anti-CD3/CD28 gen değil, one-hot'a düşer. 2 perturbation için yeterli |
| Donör temsili | Yok. Model sadece tek tek kontrol hücresini görüyor | Donör bilgisi dolaylı olarak, aynı donörün kontrol hücresinden gelir. **Açık bir donör embedding'i eklemek katkımız olabilir** |
| Ön işleme | HVG seçimi (5000 gen) tüm veride, test dahil, yapılıyor. Protein log1p-CP10k ile normalize ediliyor | HVG **sadece eğitim donörlerinde** seçilmeli. Protein için CLR daha standart |
| Kayıp fonksiyonu | Rastgele eşleşmiş hücre çiftleri arasında MSE + adversarial BCE, ağırlık 1:1 | Rastgele eşleşmeyle MSE, pratikte koşul ortalamasını öğretir. Hücre düzeyindeki varyasyonu yakalamaz |
| Metrik | Ham değerler üzerinden, hücre × gen matrisi düzleştirilip Pearson | Kontrole göre değişim (delta) ölçülmüyor. Değerler şişik çıkar. **pertbench'in delta metrikleriyle yeniden skorlanmalı** |
| Kaynak | PyTorch 2.0; makalede A100 GPU | Model küçük (birkaç milyon parametre). Lawlor boyutunda veri CPU'da da eğitilebilir |

## 4. MultiPert'te yapılacak değişiklikler

1. **Donör bazlı split:** 8 donör eğitim, 1 donör doğrulama (early stopping için), 1 donör test. 10 fold boyunca dönüyor.
2. **Donör içi eşleşme:** Her perturbe hücreye aynı donörün ve aynı hücre tipinin kontrol hücresinden eşleşme yapılacak. Testte girdi, test donörünün kendi kontrol hücreleri olacak.
3. **Sızıntıyı önleme:** HVG seçimi ve protein normalizasyon parametreleri sadece eğitim donörlerinden hesaplanacak.
4. **Değerlendirme:** Tahminler `pertbench/external.py` ile (donör × hücre tipi × koşul) pseudobulk düzeyinde, delta metrikleriyle skorlanacak. RNA ve protein ayrı raporlanacak.
5. **Baseline'lar:** Aynı fold'larda şu modeller çalıştırılacak. Hepsi pertbench'te hazır.
   - `PerturbationMean`: diğer 9 donörün ortalama cevabı
   - `Additive`
   - `ContextKNN`
   - `ContextRidge`: donörün kontrol profilinden cevabı tahmin eden lineer model
6. **Uzantılar (araştırma katkısı):**
   - (a) Donör embedding'i: donörün kontrol hücrelerinin multimodal ortalaması veya set encoder ile özeti. Perturbation embedding'ine eklenecek.
   - (b) Genotip bilgisi: VCF'ten bağışıklıkla ilgili eQTL'ler → donör vektörü.
   - (c) Few-shot: test donörünün bir perturbation'ı biliniyorsa diğerini tahmin etmek. `unseen_donor` split'inde `k_shot` desteği zaten var.

## 5. Önce cevaplanması gereken soru

**Donörler arasında, tahmin edilmeye değer bir cevap farkı var mı?** Lawlor verisinde her hücre tipi ve koşul için cevabın varyansını iki kaynağa ayıracağız:
- Perturbation'ın ortak etkisi
- Donöre özgü sapma

Donöre özgü pay çok küçükse, hiçbir model `PerturbationMean`'i anlamlı şekilde geçemez. Bunu baştan bilmek, sonuçları doğru yorumlamak için şart.

## 6. Sıradaki adımlar

| # | İş | Sorumlu (öneri) |
|---|---|---|
| 1 | Lawlor verisinin işlenmiş matrisini edinmek (portal / yazarlar / FASTQ) | Bengisu |
| 2 | Veri gelene kadar pertbench'te `unseen_donor` kurgusunu Kang 2018 / Parse pseudobulk üzerinde çalıştırmak (RNA-only ön deneme) | Atay |
| 3 | MultiPert'i orijinal haliyle Papalexi arrayed verisinde yeniden üretmek; sonra donör split'i ve donör içi eşleşmeyi eklemek | Berk + Alperen |
| 4 | Donör varyans analizi (bölüm 5) | Atay + Bengisu |
| 5 | MultiPert vs baseline'lar, 10 fold, RNA + protein. Ara rapor | Hepimiz |

## 7. Hocaya sorulacaklar
- Lawlor 2021 (JAX, Ucar lab) verisinin işlenmiş halini edinmek için bir bağlantınız var mı? Ya da başka bir çok donörlü CITE-seq stimülasyon verisi biliyor musunuz?
- Hedef donör sayısı için bir alt sınır var mı? 10 donör yeterli mi, yoksa daha büyük ama RNA-only bir veriyle (Parse, 12 donör) de desteklemeli miyiz?
- Genotip bilgisini kullanmak kapsam içinde mi?

## Kaynaklar
- Lawlor vd. 2021: https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2021.636720/full ; https://pmc.ncbi.nlm.nih.gov/articles/PMC8010670/
- OP3: https://www.omicsdi.org/dataset/geo/GSE279945
- Aquino vd. 2023: https://www.nature.com/articles/s41586-023-06422-9
- MultiPert: https://github.com/MengyuanZhaoo/MultiPert
