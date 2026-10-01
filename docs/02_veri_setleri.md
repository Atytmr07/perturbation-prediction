# Veri Setleri

"İndirildi" işaretli dosyalar `data/` altında duruyor ve `pertbench.datasets` üzerinden yüklenebiliyor.

## A. Multimodal perturbation verileri

| Veri | Teknoloji | Modalite | Ölçek | Donör | Erişim | Durum |
|---|---|---|---|---|---|---|
| Papalexi 2021 (THP-1) | ECCITE-seq | RNA + 4 protein | 20,7 bin hücre, 25 hedef gen | Yok (3 replikat) | Zenodo 10044268 (scPerturb) | **İndirildi, çalışıyor** |
| Frangieh 2021 (melanom) | Perturb-CITE-seq | RNA + 20 protein | 218 bin hücre, 248 hedef, 3 koşul | Tek hasta modeli | Zenodo 10044268 (RNA 1,5 GB) | **Protein kısmı indirildi, çalışıyor** |
| Kidney | CaRPool-seq | RNA + 7 protein | 8,8 bin hücre | Yok | GEO GSE213957 | MultiPert'te kullanılmış |
| PBMC stimülasyon | ASAP-seq / 10x Multiome | ATAC+protein / RNA+ATAC | — | Birkaç donör (doğrulanmalı) | GEO GSE156478 | MultiPert'te kullanılmış |
| Perturb-multiome | Multiome Perturb-seq | RNA + ATAC | 133 bin hücre, 10 hücre tipi, 19 TF | Yok (doğrulanmalı) | GEO GSE274113 | MultiFlow'un ana verisi |
| Multiome Perturb-seq (B hücresi) | Multiome | RNA + ATAC | — | — | Cell Systems 2024 | İncelenecek |
| Spear-ATAC / Perturb-ATAC | CRISPR + ATAC | ATAC (± RNA) | — | Yok | Pierce 2021, Rubin 2019 | İncelenecek |
| **OP3 / NeurIPS 2023** | 10x Multiome + hashtag | **RNA + ATAC (+ HTO)** | 144 ilaç × 4 hücre tipi | **3 donör** | GEO GSE279945, S3 (openproblems) | **En kritik aday:** hem multimodal hem donörlü. ATAC'ın perturbe örneklerde olup olmadığı doğrulanmalı |

## B. Çok donörlü / hasta verileri (donör ekseni)

| Veri | Perturbation | Donör | Ölçek | Erişim |
|---|---|---|---|---|
| **Parse 10M PBMC** | 90 sitokin + PBS | **12 donör** (6K/6E) | 9,7 M hücre, 18 hücre tipi | Parse Biosciences web sitesi (h5ad 41 GB; pseudobulk 6 GB, bizim için yeterli). Lisansı kontrol edilmeli |
| **iPSC CRISPRi haritası** (Cell Genomics 2025) | 7.226 gen CRISPRi | **34 iPSC hattı / 26 donör** | Genom ölçekli | Figshare (count + fold-change) |
| Genom ölçekli CD4+ T hücre Perturb-seq (bioRxiv 2025.12) | Genom ölçekli KO, dinlenme/uyarı | Çok donör | Çok büyük | bioRxiv 10.64898/2025.12.23.696273 |
| Kang 2018 PBMC | IFN-β | 8 hasta | ~25 bin hücre | pertpy / scGen verisi (figshare bot korumalı; alternatif kaynak bulunmalı) |
| OP3 | 144 ilaç | 3 donör | — | Yukarıda |

## C. RNA-only standart benchmark'lar (baseline karşılaştırması için)
- Norman 2019 (K562, kombinasyonlu CRISPRa). Zenodo'da `NormanWeissman2019_filtered.h5ad`, 0,7 GB.
- Replogle 2022 (K562/RPE1, genom ölçekli CRISPRi).
- sci-Plex (Srivatsan 2020; 3 hücre hattı, 188 ilaç).
- Tahoe-100M (50 kanser hattı, 1.100 ilaç). Çok büyük.

## Notlar
- **figshare** linkleri (pertpy'nin kullandığı) bot koruması arkasında olduğu için scriptle indirilemiyor. Aynı dosyalar **Zenodo scPerturb kaydı 10044268**'de de var. `scripts/download_data.py` bu kaydı kullanıyor.
- Papalexi'de gerçek donör yok, `donor` sütununda replikat tutuluyor. "Görülmemiş replikat" görevi "görülmemiş donör"den çok daha kolay. Nitekim bu veride donör-farkında modeller fark yaratmıyor (bkz. araştırma planı).
