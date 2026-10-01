# Okuma Haftası: MultiPert ve Multimodal Veri Entegrasyonu

*2–9 Ekim 2026. Hedef: hafta sonunda MultiPert'i satır satır anlamış olmak ve entegrasyon literatüründen MultiPert'e taşınabilecek 2–3 somut fikirle hocaya gitmek.*

## 0. Hocadan gelen yön
- Hoca 3 veri seti gönderecek. **Corona ile ilgili olanla başlayacağız.**
- Görev: multimodal veride donör değişimi. N donörün N-1'iyle eğitip kalanını tahmin etmek.
- Fikir: multimodal veri entegrasyonu literatüründeki yöntemlerle MultiPert'i geliştirmek. Hocaya göre bu yöntemler perturbation problemine uygulanmamış.

> **Güncelleme:** Hocanın gönderdiği corona verisi Aquino 2023 değil, **Zhang vd. 2023 (Nat Immunol, COVID aşısı)** çıktı. Ayrıntılar `07_hocanin_veri_setleri.md` dosyasında. Aşağıdaki Aquino notu sadece arşiv için duruyor.

### (Arşiv) İlk tahminimiz: Aquino 2023
**Aquino vd. 2023, Nature:** "Dissecting human population variation in single-cell responses to SARS-CoV-2".
- 222 sağlıklı donör (Afrika, Avrupa ve Doğu Asya kökenli).
- PBMC'ler 6 saat boyunca uyarılmamış (NS), influenza A (IAV) ile ve SARS-CoV-2 (COV) ile tutulmuş. 8 donör için ek olarak 0 ve 24. saat ölçümleri var.
- ~1 milyon hücre, tamamında scRNA-seq.
- **Protein (CITE-seq) sadece 16 örnekte var.**

**Bu bizim için ne demek?**
1. Donör ekseni çok güçlü: 222 donörle leave-one-donor-out ya da k-fold donör split yapılabilir.
2. Multimodal kısım **eksik modalite** problemi: RNA her yerde var, protein çok az örnekte. MultiPert her hücrede iki modalitenin de olmasını şart koşuyor. Bu haliyle bu veriye uymaz.
3. Entegrasyon literatüründe tam bu problem için yöntemler var: "mosaic integration", eksik modalite imputasyonu. **Hocanın işaret ettiği yön muhtemelen burası.**

### Dikkat: "perturbation'a uygulanmamış" iddiası tam doğru değil
**MultiCPA** (Inecik, Uhlmann, Lotfollahi, Theis; bioRxiv / ICML CompBio 2022) RNA + proteini iki yolla birleştirip perturbation tahmini yapıyor: concatenation ve **Product of Experts (PoE)**. Kod: theislab/multicpa.

Bu yüzden hocaya şöyle demek daha doğru olur: "Entegrasyon fikirlerinin perturbation'a uygulanması çok sınırlı kalmış (MultiCPA, MultiPert). **Eksik modalite** ve **donör genellemesi** ise hiç ele alınmamış."

## 1. MultiPert'i derinlemesine okuma

### Makale (PLOS Comput Biol 2026)
| Bölüm | Neye dikkat edilecek |
|---|---|
| Şekil 1 + Methods "Model architecture" | Encoder'lar (ZINB-VAE, AE), ortak encoder, füzyon ağı, dual attention, decoder'lar. Her bloğun girdi/çıktı boyutu |
| Methods "Adversarial alignment" | Discriminator neyi ayırt ediyor, generator nasıl kandırıyor, kayıp ağırlıkları |
| Methods "Data split" | 3:1:1 rastgele hücre bölmesi. Neden bu interpolasyon görevi? |
| Results: ablation | Hangi bileşen ne kadar katkı sağlıyor (adversarial, özel encoder'lar, füzyon stratejisi) |
| Results: unseen perturbation | GEARS'a karşı leave-one-out deneyi |
| Discussion | Yazarların kendi kabul ettiği kısıtlar |

### Kod (`external/MultiPert/code`, ~900 satır)
| Dosya | Okurken cevaplanacak soru |
|---|---|
| `data_loader.py` | Kontrol hücreleri perturbe hücrelerle nasıl eşleşiyor? (`sample_data`: rastgele.) Split nasıl? HVG nerede seçiliyor? |
| `models.py` | `ZINBVAE`, `SharedEncoderRNA`, `FusionNetwork`, attention katmanı. Toplam parametre sayısı? |
| `trainer.py` | Generator ve discriminator güncellemelerinin sırası. Early stopping hangi kayba bakıyor? |
| `metrics.py` | PCC neden ham değerler üzerinden ve düzleştirilmiş matriste hesaplanıyor? Delta metriği olsa ne değişirdi? |
| `main.py` | Uçtan uca akış. Çıktılar nereye yazılıyor? |

**Haftanın sonunda MultiPert hakkında cevaplayabilmemiz gerekenler:**
1. Model bir kontrol hücresini perturbe hücreye nasıl dönüştürüyor? Tek cümleyle.
2. Bir hücrede protein ölçümü yoksa model ne yapar? (Cevap: çalışmaz, iki girdi de zorunlu.)
3. Modelde donör bilgisi nereden girebilir?
4. Adversarial hizalama ne işe yarıyor? Yerine ne konabilir?
5. Değerlendirme neden iyimser sonuç veriyor? (Rastgele hücre bölmesi + ham değer korelasyonu.)

## 2. Multimodal entegrasyon literatürü: MultiPert'e ne taşınabilir?

| Yöntem | Yayın | Temel fikir | MultiPert'e katkısı | Öncelik |
|---|---|---|---|---|
| **totalVI** | Gayoso vd., Nat Methods 2021 | CITE-seq için ortak olasılıksal VAE. Protein = arka plan + ön plan karışımı. Batch etkisini modelliyor. Protein ölçülmemiş hücrelerde proteini impute edebiliyor | (1) Proteini MSE yerine doğru bir olasılık modeliyle modellemek. (2) Protein eksik örneklerle çalışmak. (3) Donörü kovaryat olarak almak | **Yüksek** |
| **MultiCPA** | Inecik vd., 2022 | CPA'nın multimodal hali. Concat ve PoE ile birleştirme | En yakın önceki çalışma. MultiPert'le karşılaştırılmalı | **Yüksek** |
| **Product / Mixture of Experts** (scMM, Multigrate, MultiVI) | Minoura 2021; Lotfollahi 2022; Ashuach 2023 | Her modalite kendi latent tahminini üretir, bunlar birleştirilir. Eksik modalite birleşimden çıkarılır | Adversarial hizalama yerine PoE/MoE. **Eksik modaliteyi doğal olarak destekler**, corona verisi için şart | **Yüksek** |
| **MIDAS** | He vd., Nat Biotech 2024 | Mosaic entegrasyon: farklı örneklerde farklı modalite kombinasyonları. Batch'i biyolojiden ayırma (disentangle) | Corona verisindeki "RNA her yerde, protein az yerde" yapısına birebir uyuyor | **Yüksek** |
| scVAEIT | Du vd., PNAS 2022 | Maskeleme ile eksik modalite imputasyonu | Eğitimde rastgele modalite maskeleme fikri | Orta |
| GLUE | Cao & Gao, Nat Biotech 2022 | Önsel bilgi grafiğiyle (gen ↔ peak/protein) modalite hizalama | Gen–protein eşleşmesini (ör. CD4 geni ↔ CD4 proteini) modele vermek | Orta |
| Seurat WNN | Hao vd., Cell 2021 | Her hücre için modalitelere öğrenilmiş ağırlık | Hücre bazında "hangi modaliteye ne kadar güvenelim" fikri | Orta |
| MOFA+ | Argelaguet vd., Genome Biol 2020 | Lineer faktör modeli, modaliteler arası ortak/özel faktörler | Yorumlanabilir donör faktörleri. Basit ve güçlü bir baseline | Orta |
| BABEL, sciPENN, scButterfly | 2021–2024 | Modaliteler arası çeviri (RNA → protein) | "Protein cevabını RNA cevabından tahmin et" baseline'ı (bizdeki CrossModal) | Düşük |
| StabMap | Ghazanfar vd., Nat Biotech 2024 | Kısmen örtüşen özellik setleriyle mosaic hizalama | Farklı protein panelleri olan verileri birleştirmek | Düşük |
| **scMultiBench** | Nat Methods 2025 | 40 entegrasyon yöntemini 64 veri üzerinde karşılaştıran benchmark | Hangi yöntemin hangi görevde iyi olduğunu görmek için başlangıç noktası | **Önce oku** |

## 3. Şimdiden görünen geliştirme fikirleri

Hepsi veri geldiğinde test edilecek hipotezler.

1. **Eksik modaliteye dayanıklı MultiPert:** Adversarial hizalamanın yerine PoE/MoE ile ortak latent. Model, protein ölçülmemiş donörlerden de RNA üzerinden öğrenebilir. Protein olan 16 örnek, protein decoder'ını eğitir.
2. **Donör koşullama:** Donörün kontrol hücrelerinden bir donör embedding'i (ortalama veya set encoder). Perturbation embedding'iyle birlikte dikkat katmanına girer.
   - *Dikkat:* Entegrasyon yöntemleri genelde donörü "batch" diye **siler**. Biz donöre özgü cevabı **korumak** istiyoruz. Bu ayrım projenin kilit noktası.
3. **Doğru protein olasılık modeli:** log-CP10k üzerinde MSE yerine totalVI tarzı arka plan/ön plan negatif binom.
4. **Değerlendirme:** Donör bazlı split, delta metrikleri, `PerturbationMean` baseline'ı. Bunlar pertbench'te hazır.

## 4. Haftalık iş bölümü (öneri)

| Kişi | Okuma | Hafta sonu çıktısı |
|---|---|---|
| Berk | MultiPert makalesi (tamamı) + `models.py`, `trainer.py` | 1 sayfa: mimari şeması ve 5 sorunun cevabı |
| Atay | MultiPert `data_loader.py`, `metrics.py` + scMultiBench | 1 sayfa: değerlendirme sorunları ve donör split tasarımı |
| Alperen | totalVI + MultiCPA + Multigrate/MultiVI (PoE/MoE) | 1 sayfa: PoE/MoE MultiPert'e nasıl takılır |
| Bengisu | MIDAS + scVAEIT + Aquino 2023 (veri tasarımı) | 1 sayfa: corona verisinin yapısı, eksik modalite nasıl ele alınır |

**Hafta sonu (9 Ekim) iç toplantı:** Herkes 5 dakika anlatır. Hocaya götürülecek 2–3 fikir seçilir.

## Kaynaklar
- Aquino vd. 2023: https://www.nature.com/articles/s41586-023-06422-9 ; veri özeti: https://db.cngb.org/trueblood/dataset
- MultiPert: https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1014054 ; kod: https://github.com/MengyuanZhaoo/MultiPert
- MultiCPA: https://www.biorxiv.org/content/10.1101/2022.07.08.499049v1
- totalVI: https://www.nature.com/articles/s41592-020-01050-x
- scMultiBench (Nat Methods 2025): https://www.nature.com/articles/s41592-025-02856-3 ; https://github.com/PYangLab/scMultiBench
- Seurat WNN: https://www.sciencedirect.com/science/article/pii/S0092867421005833
- scvi-tools multimodal eğitimleri: https://docs.scvi-tools.org/en/stable/tutorials/index_multimodal.html
