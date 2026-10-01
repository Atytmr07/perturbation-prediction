# Araştırma Planı (Taslak)

## Önerilen başlık
**Donör-farkında, çok modaliteli tek hücre perturbation cevabı tahmini: bir benchmark ve bir model**

## Problem tanımı
Bir donörün (hastanın) perturbe edilmemiş **multimodal** baseline örneği verilsin: RNA ve varsa protein ve/veya ATAC. İsteğe bağlı olarak genotip bilgisi de olabilir. Buna bir perturbation *p* eklenince, bu donörün hücrelerinin *p* altındaki profilini **tüm modalitelerde** tahmin et. Donör, eğitimde hiç görülmemiş olabilir veya az sayıda perturbation'ı ölçülmüş olabilir (few-shot).

## Araştırma soruları
- **AS1: Mevcut multimodal yöntemler basit baseline'ları geçiyor mu?**
  - MultiPert ve MultiFlow'u kendi veri setlerinde ve yeni veri setlerinde çalıştır.
  - PerturbationMean, Additive ve lineer baseline'larla aynı split'lerde ve aynı metriklerle karşılaştır.
  - Motivasyon: Ahlmann-Eltze vd. 2025, RNA-only modellerde bu karşılaştırmanın sonucu tersine çevirebildiğini gösterdi.
- **AS2: Görülmemiş donörde donör bilgisi ne kadar işe yarıyor?**
  - Donör × perturbation etkileşiminin büyüklüğünü ölç: donöre özgü cevabın popülasyon ortalamasından sapması.
  - Bu sapmanın, donörün baseline profilinden tahmin edilebilir kısmını ölç.
  - Veri: Parse 10M, OP3, iPSC CRISPRi.
- **AS3: İkinci modalite, RNA'nın taşımadığı bilgiyi ne ölçüde taşıyor?**
  - Protein/ATAC cevabını RNA cevabından tahmin ederek (CrossModal) modaliteye özgü sinyalin payını ölç.
- **AS4 (yöntem):** Donör temsilini multimodal baseline'dan öğrenen ve cevabı tüm modalitelerde üreten bir model geliştir.
  - Aday tasarım: CellFlow/MultiFlow tarzı koşullu flow matching.
  - Koşul vektörü: perturbation embedding'i + multimodal kontrol dağılımından (set encoder) çıkarılan donör embedding'i.
  - Few-shot uyarlama: yeni donörün birkaç ölçülmüş perturbation'ıyla embedding'i ince ayarlamak.

## Değerlendirme protokolü (`pertbench` içinde uygulandı)
**Split'ler:**
- random
- unseen_perturbation
- unseen_cell_type (leave-one-out)
- unseen_donor (leave-one-out, isteğe bağlı k-shot)

Tüm split'lerde kontroller eğitimde kalıyor.

**Metrikler:**
- Birincil: delta-Pearson, top-k DEG delta-Pearson/MSE, yön doğruluğu.
- Referans (ham profil Pearson): baseline'da bile ~0,99 çıktığı için tek başına anlamsız.
- Dağılım metrikleri (MMD, energy distance) ve modaliteler arası uyum metriği sonraki adımda eklenecek.

**Baseline'lar:**
- NoChange, GlobalMean, PerturbationMean, Additive
- ContextKNN, ContextRidge (donör-farkında)
- LinearEmbedding (Ahlmann-Eltze)
- CrossModal

## Ön sonuçlar (29.09.2026, CPU, pseudobulk)
Metrik: top-20 cevap özelliğinde delta MSE (düşük = iyi).

| Veri / split | NoChange | PerturbationMean | ContextRidge | LinearEmbedding |
|---|---|---|---|---|
| Sentetik, unseen_donor, RNA | 8,61 | 2,14 | **1,35** | 3,93 |
| Sentetik, unseen_perturbation, RNA | 4,68 | 4,88 | 4,91 | **3,29** |
| Papalexi (THP-1), unseen_replicate, RNA | 0,361 | **0,039** | **0,039** | 0,262 |
| Papalexi, unseen_replicate, protein | 0,028 | **0,007** | **0,007** | 0,024 |
| Papalexi, unseen_perturbation, RNA | 0,726 | 0,579 | **0,576** | 0,584 |
| Frangieh (protein), unseen_condition | 0,006 | **0,005** | **0,005** | — |

**Yorum:**
- Sentetik veriye kasıtlı olarak bir donör × perturbation etkileşimi koyduk. Bu etkileşim varken donör-farkında `ContextRidge`, additive baseline'a göre hatayı yaklaşık %37 azaltıyor. Yani pipeline bu sinyali yakalayabiliyor.
- Papalexi'de "donör" aslında aynı hücre hattının replikatı. Bu yüzden donör-farkında modeller hiçbir kazanç sağlamıyor. Bu, gerçek çok donörlü multimodal veriye (OP3, Parse) neden ihtiyaç olduğunu gösteriyor.
- Görülmemiş perturbation'da gerçek verilerde tüm baseline'lar birbirine yakın, NoChange'e göre kazanç da küçük. Bu, literatürdeki bulguyla tutarlı.
- Papalexi'deki unseen_perturbation split'i tek fold ve 5 perturbation'dan oluşuyor. Varyansı yüksek; çok seed ile tekrarlanmalı.

## İş planı (bitirme projesi, ~Ekim 2026 – Haziran 2027)

| Dönem | İş |
|---|---|
| Ekim | Literatür okuması (MultiPert, MultiFlow, CellFlow, Ahlmann-Eltze). `pertbench`'e dağılım metrikleri ve çok seed desteği. OP3 ve Parse pseudobulk verilerini indirip yükleyici yazmak |
| Kasım | MultiPert ve MultiFlow'u kendi verileri üzerinde yeniden üretmek (GPU: Colab/üniversite kümesi). `external.py` adaptörüyle aynı split'lerde skorlamak |
| Aralık | AS1 ve AS3: baseline'lar ve modeller × multimodal veri setleri. Ara rapor |
| Ocak | AS2: Parse/OP3/iPSC üzerinde donör etkileşimi analizi. CellFlow'u baseline olarak eklemek |
| Şubat–Mart | AS4: donör-farkında multimodal model prototipi ve ablation'lar (donör temsili: ortalama vs. set encoder vs. genotip) |
| Nisan | Son deneyler, istatistiksel testler |
| Mayıs–Haziran | Tez yazımı. Mümkünse workshop/bioRxiv makalesi |

## Riskler
- **Hesaplama:** Yerelde GPU yok. Derin modeller için Colab/üniversite GPU'su gerekiyor. Pseudobulk baseline'lar CPU'da dakikalar içinde çalışıyor.
- **Veri:** Donörlü **ve** multimodal perturbation verisi çok az. OP3'ün ATAC kısmı perturbe örneklerde yoksa AS2 ve AS3'ü ayrı veri setlerinde yürütmek gerekir.
- **Rakip çalışmalar:** Alan çok hızlı ilerliyor (2026'da en az 4 multimodal model çıktı). Benchmark katkısı, yöntem katkısından daha güvenli bir hedef.
