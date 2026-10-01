# İki İz Planı: Entegrasyon Benchmark'ı + MultiPert

*2 Ekim 2026*

Hocanın önerdiği makale:
**Fu vd., "Benchmarking single-cell multi-modal data integrations", Nature Methods 2025, 22:2437–2448. DOI: 10.1038/s41592-025-02737-9.**

## Neden iki iz birbirine bağlı?
Hocanın problemi: baseline RNA + ATAC → tedavi sonrası RNA + ATAC, görülmemiş donör için.

Üç veride de RNA ve ATAC **aynı hücrede ölçülmemiş**:
- **COVID verisi:** CITE-seq (RNA+ADT) ve ASAP-seq (ATAC+ADT) ayrı hücrelerde. Ortak köprü 173 ADT proteini.
- **Nöroblastom ve AML:** RNA ve ATAC tamamen ayrı assay'ler.

MultiPert her hücrede iki modalitenin birlikte olmasını varsayıyor. Bu yüzden önce modaliteleri ortak bir uzaya taşıyacak bir **entegrasyon katmanı** gerekiyor. Fu vd. tam olarak bu katman için hangi yöntemin iyi olduğunu söylüyor.

- **İz B (benchmark)**, MultiPert'in yeni "omurgasını" seçiyor.
- **İz A (MultiPert)**, bu omurganın üzerine perturbation ve donör modülünü kuruyor.

## Fu vd. 2025: bizim için önemli olanlar
- 40 algoritma, 65 yöntem varyantı, 14 kaynak veriden türetilmiş 101 benchmark verisi.
- Değerlendirilen görevler: embedding kalitesi, hücre hizalama, **modaliteler arası imputasyon**, sağlamlık (seyreltme, tekrarlanabilirlik), ölçeklenebilirlik.

| Kategori | Bizim verideki karşılığı | Önde çıkan yöntemler (Fu vd.) |
|---|---|---|
| **Mosaic RNA+ADT / RNA+ATAC** (bazı hücrelerde bir modalite eksik) | **COVID:** CITE (RNA+ADT) + ASAP (ATAC+ADT), ADT köprü | **MIDAS** (RNA+ADT'de açık ara önde; imputasyonda SOTA), MultiVI (en sağlam), Seurat v5 Bridge, StabMap |
| **Diagonal / eşsiz RNA+ATAC** (hiçbir hücrede iki modalite birlikte yok) | **Nöroblastom, AML** | **GLUE** (hücre hizalamada açık ara önde) |
| Eşli RNA+ATAC | Elimizde yok | Seurat v4 WNN, scMVP, scMDC |
| Eşli RNA+ADT | COVID'in CITE kısmı tek başına | totalVI, Seurat v4 WNN, bindSC |

**Makaleden bizim için kritik notlar:**
- Batch bilgisi verildiğinde doğruluk artıyor (MultiVI, Multigrate). Ancak **bizde donör "batch" değil, korunması gereken biyoloji**. Batch olarak verilecek şey assay, kütüphane veya lane olmalı, donör değil.
- Yöntemlerin sıralaması veri setine göre değişiyor. Kendi verimizde tekrar test etmek gerekiyor.
- Derin öğrenme yöntemleri sabit seed olmadan kararsız. Her deneyde birden fazla seed kullanılmalı.
- Gene activity matrisi hazırlamak, büyük verilerde diagonal yöntemleri yavaşlatıyor. Nöroblastom verisi için bunu hesaba katmak lazım.
- Makale tekrarlanabilir bir pipeline ve bir Python metrik paketi yayınlamış. Bunu doğrudan kullanabiliriz.

**Bu benchmark'ın değerlendirmediği şey:** perturbation ve donör genellemesi. Fu vd. entegrasyonu sadece kümeleme ve imputasyon üzerinden ölçüyor. **Bizim katkımız, bu yöntemleri perturbation tahmini için omurga olarak kullanıp aynı ölçütle karşılaştırmak olabilir.**

## İz B: Entegrasyon benchmark'ı (1 kişi)
**Hedef:** COVID verisinde (sonra nöroblastomda) MultiPert'in yerine geçecek entegrasyon omurgasını seçmek.

| Hafta | İş |
|---|---|
| 1 | Fu vd.'yi oku: mosaic ve diagonal bölümleri, metrikler, Supplementary'deki yöntem ayarları. Kısa liste: MIDAS, MultiVI, Seurat v5 Bridge, GLUE, totalVI (yalnızca CITE kısmı için) |
| 2 | Kısa listedeki yöntemleri COVID verisinde çalıştır: CITE + ASAP mosaic, ADT köprü. Fu vd.'nin metrik paketiyle ölç. Ek ölçüt: **donör ayrımını koruyor mu?** (Donör etiketinin embedding'den ne kadar iyi tahmin edildiği.) |
| 3 | En iyi 1–2 yöntemi İz A'ya omurga olarak teslim et. Embedding + modalite decoder'ları (imputasyon) |

**Teslim:** "Hangi entegrasyon yöntemi bu veride hem modaliteleri hizalıyor hem donör farkını koruyor?" sorusuna cevap veren 1–2 sayfalık rapor ve tablo.

## İz A: MultiPert + perturbation modülü (diğerleri)
**Hedef:** Görülmemiş donör için baseline → tedavi sonrası, multimodal tahmin.

| Hafta | İş |
|---|---|
| 1 | MultiPert'i oku ve orijinal haliyle Papalexi arrayed verisinde çalıştır (repo bu veriyle geliyor) |
| 1–2 | COVID verisini indir. Seurat `.rds` → h5ad dönüşümü (R gerekiyor). Pseudobulk: donör × gün × hücre tipi. pertbench'te leave-one-donor-out baseline'ları çalıştır (`PerturbationMean`, `ContextRidge` vb.). İlk sayılar buradan gelecek |
| 2–3 | MultiPert'i donör split'ine uyarla. Eşleşme yok, bu yüzden hücre düzeyinde değil **dağılım düzeyinde** çalışacak bir versiyon: baseline latent dağılımı + donör embedding'i → tedavi sonrası latent dağılımı |
| 3+ | İz B'nin seçtiği omurgayı tak: herkes ortak latent uzayda. Perturbation modülü latent'te çalışır, modalite decoder'ları RNA, ATAC ve ADT'yi geri üretir |

## Hedef mimari (taslak)

```
Baseline hücreleri (donör D, gün 0)              Tedavi sonrası (donör D, gün 28) ???
 CITE: RNA+ADT   ASAP: ATAC+ADT
        │              │
        └──── Entegrasyon omurgası (İz B: MIDAS / MultiVI / GLUE) ────┐
                       │                                              │
              ortak latent z (her hücre için,                          │
              hangi modalite ölçülmüş olursa olsun)                    │
                       │                                              │
      donör embedding  ←  D'nin baseline z dağılımı (set encoder)      │
                       │                                              │
      Perturbation modülü (İz A: MultiPert'in dikkat bloğu /           │
      flow matching / OT) : z_baseline + donör + gün → z_sonrası       │
                       │                                              │
              modalite decoder'ları → RNA, ATAC, ADT  ────────────────┘
                                         (değerlendirme: pseudobulk delta, LODO)
```

## Hemen yapılabilecekler
- COVID verisi Zenodo'da açık: `PBMC_vaccine_CITE.rds` 1,6 GB, `PBMC_vaccine_ASAP.rds` 4,7 GB. Peak'ler gerekirse fragments dosyası 12,4 GB.
- Bilgisayarda **R kurulu değil**. Seurat nesnelerini okumak için R + Seurat + SeuratDisk (veya zellkonverter) gerekiyor. Alternatif olarak dönüşüm Colab'de R kernel'i ile yapılabilir.
- Fu vd.'nin pipeline'ı ve metrik paketi: makalenin "Code availability" bölümünden alınacak.

## Kaynaklar
- Fu vd. 2025 (bioRxiv versiyonu): https://www.biorxiv.org/content/10.1101/2025.04.01.646578v1.full ; DOI: 10.1038/s41592-025-02737-9
- MIDAS: He vd., Nat Biotech 2024
- GLUE: Cao & Gao, Nat Biotech 2022
- MultiVI: Ashuach vd., Nat Methods 2023
- COVID verisi: https://zenodo.org/records/7555405
