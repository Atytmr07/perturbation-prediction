# Literatür Taraması: Tek Hücre Perturbation Response Prediction

*Hazırlanma: 29 Eylül 2026. Kaynaklar sonda. "Doğrulanmalı" etiketi taşıyan bilgiler birincil kaynaktan kontrol edilmedi.*

## 1. Problem

Bir hücre topluluğunun kontrol (perturbe edilmemiş) profili ve bir perturbation (gen knock-out/CRISPRi, ilaç, sitokin) verildiğinde, perturbe edilmiş topluluğun profilini tahmin et. Değerlendirmede tipik genelleme eksenleri:

| Eksen | Soru | Zorluk |
|---|---|---|
| Görülmemiş perturbation | Hiç ölçülmemiş bir geni KO edersek ne olur? | En zor; derin modeller basit baseline'ları çoğu zaman geçemiyor |
| Görülmemiş bağlam (hücre tipi) | Bu ilacın T hücresindeki etkisini biliyoruz, B hücresinde ne olur? | Orta |
| Görülmemiş donör/hasta | Yeni bir hastanın kontrol örneği var, cevabını tahmin et | Klinik açıdan en anlamlı; az çalışılmış |
| Kombinasyon | A ve B tekil etkileri bilinirken A+B'nin etkisi ne olur? | Orta-zor |

## 2. Hocanın verdiği iki makale

### 2.1 MultiPert (PLOS Comput Biol, Mart 2026)
Zhao, Tang, Li, Liang, Tang, Guo. *"MultiPert: An adversarial alignment and dual attention framework for single-cell multi-omics perturbation prediction."* DOI: 10.1371/journal.pcbi.1014054. Kod: <https://github.com/MengyuanZhaoo/MultiPert>

- **Modaliteler:** RNA + protein (ADT). Ek deneylerde RNA+ATAC ve ATAC+protein de var.
- **Mimari:** Modaliteye özgü encoder'lar ve ortak bir encoder var. Adversarial discriminator, latent uzayda modaliteleri hizalıyor. Ardından cross-attention + channel attention (dual attention) ve modaliteye özgü decoder'lar geliyor. RNA tarafı ZINB-VAE ile, protein tarafı AE ile önceden eğitiliyor. Perturbation embedding'i GEARS'taki GO grafiği ve GNN'den alınıyor.
- **Veri:** THP-1 ECCITE-seq (8.984 hücre, 4 protein, 9 KO; Zenodo 10.5281/zenodo.7041849). Kidney CaRPool-seq (GSE213957; 7 protein, 7 perturbation). PBMC ASAP-seq / 10x Multiome (GSE156478; stimülasyon deneyi).
- **Baseline'lar:** scGen, CPA, scPRAM, scGPT, CoupleVAE, GEARS.
- **Metrikler:** MSE ve PCC (tüm genler ve top-50 DEG).
- **Sonuç:** THP-1'de top-50 DEG PCC 0,88. İyileşme ikinci en iyi yönteme göre %2–7 civarında.
- **Zayıf yönler (bizim yorumumuz):**
  - Protein paneli çok küçük (4–7 protein).
  - Perturbation sayısı az (7–9).
  - Hiçbir donör ekseni yok.
  - Ahlmann-Eltze tipi lineer/additive baseline'larla karşılaştırma yok.

### 2.2 MultiFlow (bioRxiv, Ağustos 2026)
Wang, Zhang, Zhang, Nie, Liu (Yale/Stanford). *"MultiFlow: coupled flow matching for predicting single-cell multiomic perturbation responses in unseen cellular contexts."* DOI: 10.64898/2026.08.20.746112. Kod: <https://github.com/liuq-lab/MultiFlow>

- **Modaliteler:** RNA + ATAC (eşleşmiş multiome).
- **Mimari:**
  - Her modalite için autoencoder, 128 boyutlu latent.
  - İki bağlı (coupled) koşullu hız alanı (flow matching) aynı Gauss gürültüsünden başlıyor.
  - Çift yönlü "Cross Flow Module"ler cross-attention ile modaliteler arasında bilgi aktarıyor.
  - Bağlam ve perturbation embedding'leriyle modüle edilen residual bloklar var.
  - Perturbation'a özgü bir debiasing adımı var.
- **Veri:** Perturb-multiome (GSE274113; 133.022 hücre, 10 hematopoietik hücre tipi, 19 TF KO). Üretim benchmark'ları için OpenProblems multiome ve PBMC10k.
- **Görev:** Görülmemiş **hücre tipinde** cevap tahmini.
- **Baseline'lar:** scGen, trVAE, scPreGAN, CellOT, biolord, inVAE, TxPert, MultiPert, regresyon baseline'ları.
- **Metrikler:**
  - Ortalama profil: Pearson/Spearman, MSE.
  - Dağılım: MMD, iLISI.
  - Perturbation'a özgü: PCC-delta, delta-MSE, cosine, yön doğruluğu.
  - Modaliteler arası: peak–gene effect concordance, RNA–ATAC komşuluk uyumu.
- **Yazarların kabul ettiği kısıtlar:**
  - Tek bir multiomik perturbation kaynağında doğrulanmış.
  - Mimari tam olarak 2 modaliteye göre tasarlanmış.
  - Kurulan ilişkiler nedensel değil, ilişkisel.

## 3. Alanın haritası

| Yöntem | Yıl / Yer | Temel fikir | Modalite | Donör/hasta | Görülmemiş pert. |
|---|---|---|---|---|---|
| scGen | 2019 Nat Methods | VAE latent aritmetiği | RNA | Bağlam transferi (Kang PBMC hastaları), donör özelliği yok | Hayır |
| CPA / chemCPA | 2023 Mol Syst Biol | Kompozisyonel AE, kovaryat embedding'i | RNA | Donör kategorik kovaryat olabilir, yeni donöre genelleyemez | Kısmen (ilaç) |
| CellOT | 2023 Nat Methods | Nöral optimal transport | RNA | Hasta dışı tutma deneyleri | Hayır |
| GEARS | 2023 Nat Biotech | GO gen grafiği + GNN | RNA | Yok (tek hücre hattı) | Evet (genetik) |
| biolord | 2024 Nat Biotech | Atribüt ayrıştırma (disentanglement) | RNA | Atribüt olarak olabilir | Kısmen |
| scPRAM | 2024 Bioinformatics | VAE + OT + attention | RNA | Bireyler arası transfer | Hayır |
| scGPT / Geneformer | 2024 | Foundation model, fine-tune | RNA | Yok | Evet (iddia) |
| Lineer baseline (Ahlmann-Eltze vd.) | 2025 Nat Methods | Gen/pert. embedding'li lineer model | RNA | Yok | Evet. **Derin modeller bunu geçemiyor** |
| **CellFlow** (Klein, Theis vd.) | 2025 bioRxiv | Flow matching + esnek koşul kodlama | RNA | **Evet:** donörün kontrol ortalaması donör temsili olarak kullanılıyor, Parse 10M PBMC'de görülmemiş donör deneyi var | Evet |
| scPILOT | 2026 Adv Sci | Latent OT ile cevap transferi | RNA | Hasta dışı tutma (Kang). Donör etiketi modele **girdi olarak verilmiyor** | Hayır |
| MultiPert | 2026 PLOS CB | Adversarial hizalama + dual attention | RNA+protein | Yok | LOO (GEARS'a karşı) |
| MultiFlow | 2026 bioRxiv | Bağlı flow matching | RNA+ATAC | Yok (hücre tipi transferi) | Hayır |
| CLM-X | 2026 bioRxiv | Multiway Transformer foundation model | RNA, ATAC, RNA+ATAC | Yok | Genetik pert. görevi var |
| CellxPert | 2026 arXiv | Multi-omik FM + MCMC ile in-silico pert. | RNA+ATAC+protein | Yok | In-silico |

Ayrıca TxPert, State (Arc Institute), PerturbNet, scLAMBDA, SCCVAE ve PrePR-CT de var. Bunlar RNA odaklı ve donör ekseni içermiyor (doğrulanmalı).

### Önemli benchmark çalışmaları
- **Ahlmann-Eltze, Huber, Anders (Nat Methods 2025, 22:1657):** GEARS, scGPT, scFoundation ve diğer derin modeller, görülmemiş genetik perturbation'larda additive ve lineer baseline'ları geçemiyor. **Kendi çalışmamızda bu baseline'lar zorunlu olmalı.**
- **"Benchmarking algorithms for generalizable single-cell perturbation response prediction" (Nat Methods 2025):** 27 yöntem, 29 veri seti, 6 metrik.
- **"A Systematic Comparison of Single-Cell Perturbation Response Prediction Models" (bioRxiv 2024.12.23.630036):** 13 yöntem, 25 veri seti, 24 metrik. Görülmemiş pert., kombinasyon ve hücre tipi transferi eksenlerini kapsıyor.
- **OP3 / NeurIPS 2023 (NeurIPS 2024 D&B):** PBMC, 144 ilaç, 3 donör. Görev: görülmemiş hücre tipine genelleme.

## 4. Boşluklar ve hocanın hipotezinin değerlendirmesi

**Hipotez 1: "Multi-modal için boşluk var." Doğru.**
- Multimodal perturbation modelleri 2026'da daha yeni çıkıyor (MultiPert, MultiFlow, CLM-X, CellxPert).
- Bu modellerin değerlendirmesi dar: az sayıda veri seti, az protein, az perturbation.
- Basit baseline'larla adil bir karşılaştırma yapılmamış.
- Modaliteler arası sistematik bir benchmark yok.

**Hipotez 2: "Donör bilgisini dahil eden yöntem yok." Kısmen doğru, düzeltilmesi gerekiyor.**
- CellFlow, donörü kontrol hücrelerinin ortalamasıyla temsil ediyor ve Parse 10M PBMC verisinde (12 donör, 90 sitokin) *görülmemiş donörler* için tahmin yapıyor.
- CPA ve biolord donörü kovaryat olarak alabiliyor.
- scGen, scPRAM ve scPILOT hasta dışı tutma deneyi yapıyor.

Buna göre gerçekten açık kalan noktalar:
1. **Donör-farkında + multimodal model yok.** CellFlow yalnızca RNA ile çalışıyor. MultiPert ve MultiFlow'da donör ekseni hiç yok.
2. **Donör temsili ilkel.** CellFlow kontrol ortalamasını kullanıyor. Genotip/eQTL bilgisi, kontrol dağılımının tamamı veya multimodal baseline kullanan bir yaklaşım yok (doğrulanmalı).
3. **Donör × perturbation etkileşimi ölçülmemiş.** "Yeni donörün cevabı popülasyon ortalamasından ne kadar sapıyor, bu sapma baseline profilinden tahmin edilebilir mi?" sorusu sistematik olarak sorulmamış.
4. **Görülmemiş donör için baseline'larla benchmark yok.** Kullanılabilecek veri setleri var: Parse 10M, OP3, 34 iPSC hattı CRISPRi haritası, genom ölçekli CD4+ T hücre Perturb-seq.

## Kaynaklar
- MultiPert: https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1014054
- MultiFlow: https://www.biorxiv.org/content/10.64898/2026.08.20.746112v1.full
- Ahlmann-Eltze vd. 2025 / benchmark: https://www.nature.com/articles/s41592-025-02980-0
- Systematic comparison: https://www.biorxiv.org/content/10.1101/2024.12.23.630036.full.pdf
- CellFlow: https://www.biorxiv.org/content/10.1101/2025.04.11.648220v1
- scPILOT: https://pmc.ncbi.nlm.nih.gov/articles/PMC13525497/
- scPRAM: https://academic.oup.com/bioinformatics/article/40/5/btae265/7646141
- CLM-X: https://www.biorxiv.org/content/10.64898/2026.02.17.704943v1.full.pdf
- CellxPert: https://arxiv.org/abs/2605.00930
- OP3: https://openproblems.bio/benchmarks/perturbation_prediction/ , https://github.com/openproblems-bio/task_perturbation_prediction
- Model kütüphanesi: https://github.com/xianglin226/Benchmarking-Single-Cell-Perturbation
