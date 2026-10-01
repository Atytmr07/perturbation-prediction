# Hocanın Gönderdiği Problem ve 3 Veri Seti

*2 Ekim 2026*

## Problem (hocanın tanımı)
> Can we predict a multiomic perturbation response in a completely unseen donor using that donor's untreated baseline cells?

| | Baseline | İlaç/tedavi sonrası |
|---|---|---|
| Hasta A, B, C | RNA + ATAC | RNA + ATAC |
| Hasta D | RNA + ATAC | **??? tahmin et** |

## Üç verinin karşılaştırması

| | **COVID aşı** (Zhang vd., Nat Immunol 2023) | **Nöroblastom** (Yu vd., Nat Genet 2025) | **Pediatrik AML** (Lambo vd., Cancer Cell 2023) |
|---|---|---|---|
| "Perturbation" | BNT162b2 aşısı. Gün 0 → 2, 10, 28 | İndüksiyon kemoterapisi (3–4 kür). Tanı biyopsisi → cerrahi rezeksiyon | Tedavi. Tanı → remisyon / nüks |
| Donör / hasta | **6** sağlıklı donör | **22** hasta | **28** hasta |
| RNA | CITE-seq (RNA + ADT), ~114 bin hücre, 24 örnek | snRNA-seq, **22 eşli** (öncesi/sonrası), ~373 bin çekirdek | scRNA-seq, ~330 bin hücre |
| ATAC | ASAP-seq (ATAC + ADT), aynı 24 örnek | snATAC-seq: **13 eşli + 7 eşsiz**, ~144 bin çekirdek | scATAC-seq, ~354 bin hücre |
| RNA ve ATAC aynı hücrede mi? | **Hayır.** Aynı örneğin farklı aliquot'ları. Köprü: iki assay'de ortak **173 ADT proteini** | **Hayır.** Ayrı assay'ler | **Hayır.** Ayrı assay'ler |
| Ek bilgi | Sağlıklı, kontrollü tasarım. ECCITE-seq ile TCR | **WGS** (hasta genomu → donör temsili için kullanılabilir). CODEX | Alt tipler (MLL, CBFB, RUNX1 füzyonları, FLT3-ITD) |
| Erişim | **Açık:** Zenodo 7555405 (CC-BY). `PBMC_vaccine_CITE.rds` 1,6 GB, `PBMC_vaccine_ASAP.rds` 4,7 GB, fragments 12,4 GB. Ham veri: dbGaP phs003322 | HTAN `hta4_2025_nature-genetics_wenbao-yu`. İşlenmiş snRNA CELLxGENE'de (`cee845e3-…`). ATAC ve WGS'in erişim koşulu kontrol edilmeli | İşlenmiş veri **açık:** GEO GSE235063 (RNA), GSE235308 (ATAC). Ham veri: EGA (kontrollü) |
| Problem tanımına uyum | İyi. Temiz ve longitudinal, ama sadece 6 donör ve etki küçük alt popülasyonlarda (antijene özgü CD8 T) | **En birebir uyan:** hasta + ilaç + RNA/ATAC, öncesi/sonrası. Ama doku örneklemesi değişiyor (biyopsi ≠ rezeksiyon) ve tümör içeriği tedaviyle büyük ölçüde değişiyor | En zayıf. "Remisyon" hücreleri lösemi hücrelerinin cevabı değil, büyük ölçüde normal kemik iliği. Nüks sadece hastaların bir kısmında |
| Rol önerisi | **Başlangıç verisi** (hocanın önerisi). Pipeline'ı kurmak için | Ana hedef / ikinci aşama | Opsiyonel / ek doğrulama |

## Üç veride ortak, kritik bir metodolojik nokta
**Üç veride de RNA ve ATAC aynı hücrede ölçülmemiş.** Bunun iki sonucu var:

1. **MultiPert doğrudan uygulanamaz.** MultiPert her hücrede iki modalitenin birlikte ölçülmüş olmasını varsayıyor ve kontrol hücresini perturbe hücreyle eşleştiriyor. Burada ne modaliteler hücre düzeyinde eşli, ne de öncesi/sonrası hücreleri eşli (farklı zaman noktaları, farklı hücreler).
2. **Hocanın bahsettiği "multimodal data integration" tam bu boşluğu kapatıyor.**
   - COVID verisinde ADT ortak bir köprü modalite. Bridge/diagonal integration ile RNA ve ATAC aynı latent uzaya taşınabilir (ör. MultiVI, MIDAS, Seurat bridge, GLUE).
   - Nöroblastom ve AML'de köprü yok. ATAC'tan çıkarılan **gene activity** skorları veya GLUE tarzı gen–peak önsel grafiği kullanılabilir.

**Değerlendirme dağılım veya pseudobulk düzeyinde yapılmalı.** Hücre düzeyinde "bu hücre tedavi sonrası şöyle olur" diye bir eşleşme yok. Bunun yerine şu ölçülecek: "Donör D'nin hücre tipi X'inin tedavi sonrası ortalama profili ve dağılımı". pertbench bu kurguyu zaten destekliyor: `perturbation` = zaman noktası, `control` = baseline, `donor` = hasta.

## COVID verisiyle ilk deney (önerilen)
1. `PBMC_vaccine_CITE.rds` ve `PBMC_vaccine_ASAP.rds` indirilecek. Bunlar Seurat nesneleri, R ile okunup h5ad'e çevrilecek.
2. Pseudobulk birimi: donör × gün × hücre tipi. RNA, ADT (iki assay'den) ve ATAC (gene activity veya peak'ler).
3. Görev: 5 donörle eğit, 6. donörün gün 0 profilinden gün 2/10/28 profilini tahmin et. 6 fold.
4. Baseline'lar (pertbench): `NoChange`, `PerturbationMean` (diğer 5 donörün ortalama değişimi), `ContextKNN`, `ContextRidge`.
5. İlk soru: Donörler arası cevap farkı, ölçüm gürültüsünden büyük mü? Sadece 6 donör olduğu için bu soru özellikle önemli.

## Kaynaklar
- Zhang vd. 2023: https://www.nature.com/articles/s41590-023-01608-9 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC9900816/ ; Zenodo: https://zenodo.org/records/7555405
- Yu vd. 2025: https://www.nature.com/articles/s41588-025-02158-6 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC12081299 ; kod: https://zenodo.org/records/14728432
- Lambo vd. 2023: https://www.cell.com/cancer-cell/fulltext/S1535-6108(23)00364-1 ; GEO: GSE235063, GSE235308
