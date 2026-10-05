# Proje Bağlamı: Donör-Farkında Multimodal Perturbation Tahmini

*Son güncelleme: 1 Ekim 2026. Bu dosya, projeye yeni katılan birinin (veya bir AI asistanının) tüm kararları, hocanın isteklerini ve mevcut durumu tek yerden öğrenmesi için yazıldı. Daha ayrıntılı dokümanlar `docs/` altında. Bu dosya ile onlar çelişirse **bu dosya günceldir**.*

---

## 1. Kimler, ne yapıyoruz

- **Ders:** CS4001 Bitirme Projesi (Bilgisayar Mühendisliği). Araştırma odaklı proje.
- **Danışman:** Hilal Kazan. Talebimizi kabul etti.
- **Ekip:** Hasan Berk Berber, Emre Atay Tümer, Alperen Çantay, Bengisu Atlı.
- **Resmi proje adı (forma yazılan):** *Donor-Aware Multimodal Single-Cell Perturbation Response Prediction: Benchmarking and Model Development*
- **Repo (public):** https://github.com/Atytmr07/perturbation-prediction
- **Çalışma dili:** Türkçe. Dokümanlar Türkçe; kod, yorumlar ve commit mesajları İngilizce ya da Türkçe olabilir.

## 2. Araştırma problemi (hocanın tanımı)

> **Can we predict a multiomic perturbation response in a completely unseen donor using that donor's untreated baseline cells?**

| | Baseline (tedavi öncesi) | Tedavi / ilaç sonrası |
|---|---|---|
| Hasta A, B, C … (eğitim) | RNA + ATAC | RNA + ATAC |
| **Hasta D (test)** | RNA + ATAC | **??? tahmin edilecek** |

- **Değerlendirme:** leave-one-donor-out (**LODO**). Her donör sırayla test edilir, kalanlarla eğitilir. Hocanın örneği: "10 donörün 9'uyla eğit, 10.'yu tahmin et".
- **Geçilmesi gereken çıta:** `PerturbationMean` baseline'ı. Yani "yeni donör, diğer donörlerin ortalama değişimi kadar değişir" tahmini. Bunu geçemeyen model, donöre özgü bir şey öğrenmemiş demektir.

## 3. Hocanın istekleri, kronolojik

1. **İlk mail:** Perturbation prediction "hot topic". Tek modalite (scRNA-seq) için çok model var, **multimodal için boşluk var**. Hasta verisi çoğalacak; **donör bilgisini dahil eden yöntem yok gibi**. İlk hedef: mevcut yöntemleri çalıştırmak, karşılaştırmak, yeni veri setlerinde denemek. Gönderdiği iki makale: MultiPert ve MultiFlow.
2. **MultiPert ve MultiFlow'u araştırıp karşılaştırmamızı istedi.**
3. **Odak donör değişimi:** multimodal veride N–1 donörle eğitip kalan donörü tahmin etmek.
4. **MultiFlow şimdilik kapsam dışı; MultiPert'e odaklanıyoruz.**
5. Hoca **3 veri seti gönderdi**, **önce corona (COVID) verisiyle başlamamızı** önerdi.
6. **1 hafta MultiPert okuyalım.** Multimodal veri entegrasyonu üzerine araştırmalar var ama perturbation'a uygulanmamış; **bunları araştırıp MultiPert'i geliştirebiliriz.**
7. Önerdiği kaynak: **Fu vd. 2025, "Benchmarking single-cell multi-modal data integrations", Nature Methods 22:2437–2448, DOI 10.1038/s41592-025-02737-9.** Buradaki yöntemlerle MultiPert geliştirilecek. Ekipten **bir kişi bu benchmark makalesine odaklanacak**, iki iz paralel yürüyecek.

## 4. Araştırırken düzelttiğimiz varsayımlar (önemli)

| Varsayım | Gerçek durum |
|---|---|
| "Donör bilgisini dahil eden yöntem yok" | **Kısmen yanlış.** CellFlow (Klein, Theis vd., bioRxiv 2025.04.11.648220) donörü kontrol hücrelerinin ortalama ifadesiyle temsil ediyor ve Parse 10M PBMC verisinde (12 donör, 90 sitokin) görülmemiş donörü tahmin ediyor. **Ama yalnızca RNA ile.** Asıl açık nokta: **donör-farkında + multimodal** birlikte yapan yöntem yok. Hocaya bu kibarca söylenecek. |
| "Entegrasyon yöntemleri perturbation'a uygulanmamış" | **Kısmen yanlış.** MultiCPA (Inecik, Uhlmann, Lotfollahi, Theis; bioRxiv 2022.07.08.499049) RNA + proteini Product of Experts ile birleştirip perturbation tahmini yapıyor. Doğru ifade: "çok sınırlı uygulanmış; **eksik modalite** ve **donör genellemesi** ele alınmamış." |
| Corona verisi = Aquino vd. 2023 (222 donör) | **Yanlış tahmindi.** Hocanın gönderdiği veri **Zhang vd. 2023, Nat Immunol (COVID aşısı)**. Aquino sadece aday listesinde kaldı. |
| OP3 / NeurIPS 2023 multimodal, donörlü bir veri | ATAC **sadece baseline'da** var, perturbe örneklerde yalnızca RNA; 3 donör. Kurgumuza uymuyor. |

## 5. Hocanın gönderdiği 3 veri seti

| | **COVID aşı** (başlangıç verisi) | **Nöroblastom** (ana hedef, sonra) | **Pediatrik AML** (opsiyonel) |
|---|---|---|---|
| Makale | Zhang vd., *Nat Immunol* 2023: "Multimodal single-cell datasets characterize antigen-specific CD8+ T cells across SARS-CoV-2 vaccination and infection" | Yu (Wenbao) vd., *Nat Genet* 2025: "Longitudinal single-cell multiomic atlas of high-risk neuroblastoma…" | Lambo vd., *Cancer Cell* 2023: "A longitudinal single-cell atlas of treatment response in pediatric AML" |
| "Perturbation" | BNT162b2 aşısı: gün 0 → 2, 11, 28 | İndüksiyon kemoterapisi (3–4 kür): tanı biyopsisi → cerrahi rezeksiyon | Tedavi: tanı → remisyon / nüks |
| Donör | **6** sağlıklı donör | **22** hasta (öncesi/sonrası eşli) | **28** hasta |
| RNA | CITE-seq (RNA + ADT), ~114 bin hücre, 24 örnek | snRNA-seq, 22 eşli, ~373 bin çekirdek | scRNA-seq, ~330 bin hücre |
| ATAC | ASAP-seq (ATAC + ADT), aynı 24 örneğin **farklı aliquot'ları** | snATAC-seq, 13 eşli + 7 eşsiz, ~144 bin çekirdek | scATAC-seq, ~354 bin hücre |
| Köprü | **173 ortak ADT proteini** (iki assay'de de ölçülmüş) | Yok; ayrıca **WGS** var (donör temsili için kullanılabilir) | Yok |
| Erişim | **Açık:** Zenodo 7555405 (CC-BY-4.0). `PBMC_vaccine_CITE.rds` 1,6 GB, `PBMC_vaccine_ASAP.rds` 4,7 GB, `PBMC_vaccine_ASAP_fragments.tsv.gz` 12,4 GB, `PBMC_vaccine_ECCITE_TCR.rds` 0,4 GB. Ham veri dbGaP phs003322 | HTAN `hta4_2025_nature-genetics_wenbao-yu`; işlenmiş snRNA CELLxGENE `cee845e3-ec04-4781-9e2a-28734bb4f7ba`. ATAC/WGS erişimi kontrol edilecek. Kod: Zenodo 14728432 | İşlenmiş **açık:** GEO GSE235063 (RNA), GSE235308 (ATAC). Ham: EGA EGAS00001007323 |
| Uyum | Temiz tasarım, ama sadece 6 donör. Aşı etkisi küçük alt popülasyonlarda (antijene özgü CD8 T, gün 28) | Probleme en birebir uyan. Ama doku örneklemesi değişiyor ve tümör içeriği tedaviyle büyük ölçüde değişiyor | En zayıf: remisyon hücreleri ilacın cevabı değil, büyük ölçüde normal kemik iliği |

### En kritik metodolojik nokta
**Üç veride de RNA ve ATAC aynı hücrede ölçülmemiş**, tedavi öncesi ve sonrası hücreler de eşli değil. Bu yüzden:
- **MultiPert doğrudan uygulanamaz.** MultiPert, her hücrede iki modalitenin birlikte ölçüldüğünü ve kontrol–perturbe hücre eşleşmesini varsayıyor.
- **Önce bir entegrasyon katmanı gerekiyor** (hocanın Fu vd.'yi önermesinin sebebi). COVID verisi **mosaic** senaryosu (köprü ADT); nöroblastom ve AML **diagonal** senaryosu (hiç ortak ölçüm yok).
- **Değerlendirme pseudobulk ve dağılım düzeyinde yapılmalı** (donör × gün × hücre tipi). Hücre düzeyinde eşleşme yok.

## 6. MultiPert: kod düzeyinde bulgular

Zhao vd., *PLOS Comput Biol* 2026 (DOI 10.1371/journal.pcbi.1014054). Kod: github.com/MengyuanZhaoo/MultiPert (~900 satır PyTorch). Yerelde `external/MultiPert/` altında; git'e dahil değil.

- **Mimari:** RNA için ZINB-VAE, protein için AE (latent 32 boyut). Her modaliteye özel encoder + ortak (shared) encoder → fusion ağı → dual attention (cross-attention + channel attention; perturbation embedding'iyle) → modaliteye özel decoder'lar. Adversarial discriminator, ortak özelliklerin hangi modaliteden geldiğini ayırt etmeye çalışıyor. Perturbation embedding'i GEARS GO grafiğinden (64 boyut); gen olmayan perturbation'da one-hot.
- **Veri:** Repo, Papalexi 2021 **arrayed** ECCITE-seq verisiyle geliyor (THP-1, 4 protein, 9 KO). Makalede ayrıca kidney CaRPool-seq.
- **Zayıf noktalar** (bizim kurguya göre):
  1. **Kontrol–perturbe eşleşmesi rastgele** (`sample_data`). Tüm kontrol havuzundan seçiliyor, donörler karışıyor.
  2. **Split interpolasyon:** her perturbation'ın hücreleri 60/20/20 bölünüyor (`split_dataset`). Testteki perturbation eğitimde de görülmüş oluyor.
  3. **Donör girdisi yok.**
  4. **Sızıntı:** HVG (5000 gen) test dahil tüm veride seçiliyor. Protein log1p-CP10k ile normalize ediliyor (CLR değil).
  5. **Kayıp:** rastgele eşleşmiş çiftler üzerinde MSE + adversarial BCE (1:1). Pratikte koşul ortalamasını öğretir.
  6. **Metrik iyimser:** PCC, ham değerler üzerinden ve düzleştirilmiş hücre × gen matrisinde hesaplanıyor; delta (değişim) ölçülmüyor. "Hiç değişmez" diyen model bile yüksek korelasyon alır.
  7. **Eksik modalite desteklenmiyor:** her hücrede iki girdi zorunlu.
- Makaledeki eğitim ayarları: lr generator 0.001, discriminator 0.002; early stopping patience 20; en fazla 1000 epoch; batch 512; A100 GPU. Model küçük, CPU'da da eğitilebilir.

## 7. MultiFlow (kapsam dışı, ama bilinmesi gereken bulgu)

Wang vd., bioRxiv 2026 (DOI 10.64898/2026.08.20.746112). Kod: github.com/liuq-lab/MultiFlow. RNA + ATAC, bağlı flow matching, görülmemiş **hücre tipi** görevi, Perturb-multiome (GSE274113) verisi.

**Kritik bulgu:** Kodda (`paper.py`, `debias_perturbation_h5mu`) örnekleme sonrası uygulanan "debiasing", üretilen grubun latent ortalamasını **"held-out kontrol ortalaması + bu perturbation'ın eğitimdeki ortalama etkisi"**ne eşitliyor. Yani ortalama düzeyindeki metrikler, latent uzayda **PerturbationMean baseline'ının ta kendisini** ölçüyor; flow sadece dağılımın şeklini belirliyor. Ayrıca autoencoder tüm veride eğitilmiş, yazarlar da bunu belirtiyor. Perturbation embedding'i öğrenilebilir lookup tablosu olduğu için görülmemiş perturbation'a genelleyemiyor.

## 8. Fu vd. 2025 entegrasyon benchmark'ı: bizim için önemli olanlar

- 40 algoritma / 65 yöntem varyantı, 14 kaynak veriden türetilmiş 101 benchmark verisi.
- Değerlendirilen görevler: embedding, hücre hizalama, modaliteler arası imputasyon, sağlamlık, ölçeklenebilirlik. Tekrarlanabilir pipeline ve Python metrik paketi var.
- **Bizim verilere uyanlar:**
  - **Mosaic RNA+ADT / RNA+ATAC (COVID):** MIDAS (RNA+ADT'de açık ara önde, imputasyonda SOTA), MultiVI (en sağlam), Seurat v5 Bridge, StabMap.
  - **Diagonal RNA+ATAC (nöroblastom, AML):** GLUE (hücre hizalamada açık ara önde).
  - Eşli RNA+ADT: totalVI, Seurat v4 WNN. Eşli RNA+ATAC: Seurat v4 WNN, scMVP.
- Batch bilgisi verilince doğruluk artıyor. **Ama bizde donör "batch" değil, korunması gereken biyoloji.** Batch olarak assay (CITE/ASAP) veya kütüphane verilmeli, **donör asla verilmemeli**.
- Yöntem sıralaması veriye göre değişiyor. Derin öğrenme yöntemleri seed'e duyarlı.
- **Benchmark perturbation'ı değerlendirmiyor.** Entegrasyon yöntemlerini perturbation tahmininin omurgası olarak kullanıp karşılaştırmak bizim katkımız olabilir.
- R kullanmadığımız için Seurat v5 Bridge kapsam dışı.

## 9. Hedef mimari (taslak)

```
Baseline hücreleri (donör D, gün 0): CITE (RNA+ADT) + ASAP (ATAC+ADT)
   → Entegrasyon omurgası (MIDAS / MultiVI; nöroblastomda GLUE): her hücre için ortak latent z
   → Donör embedding'i: D'nin baseline z dağılımından (önce ortalama, sonra set encoder)
   → Perturbation modülü (MultiPert'in dikkat bloğundan; kayıp MMD/OT): z_baseline + donör + gün → z_sonrası (dağılım)
   → Modalite decoder'ları → RNA, ATAC, ADT
   → Değerlendirme: pseudobulk delta metrikleri + dağılım metrikleri, LODO
```

## 10. Çalışma düzeni ve kurallar

- **Kod merkezi: Atay'ın PC'si** (Windows, 64 GB RAM, Intel Ultra 7 155U CPU, NVIDIA GPU yok). Kod, veri ve deneyler burada çalışıyor.
- **Araştırma: Berk, Alperen, Bengisu** kendi PC'lerinden, AI destekli.
- **Teslim formatı:** `research/<isim>/<konu>.md`, şablon `research/SABLON.md`. Bölümler: özet, kaynaklı bulgular, uygulama bilgisi (kurulum, girdi, çıktı, GPU/RAM, örnek kod), projeye öneri, **kod merkezine iş**, açık sorular. WhatsApp'ta kalan bilgi kaybolur.
- **AI kuralları:**
  1. Her iddiaya birincil kaynak linki (makale, GitHub, resmi dokümantasyon).
  2. Sayılar ve atıflar kaynaktan kontrol edilir; AI uydurabiliyor.
  3. Kod örnekleri resmi dokümantasyondan alınır, fonksiyon adları güncel versiyonda kontrol edilir.
  4. Emin olunmayan her şey "Açık sorular"a yazılır.
- **R kullanmıyoruz.** Her şey Python. Seurat `.rds` dosyaları `py8rds` ile okunuyor (yedek: `readseurat`; o da olmazsa tek seferlik Colab dönüşümü).
- **GPU:** Okul PC'si (RTX 5070, Blackwell sm_120 → **PyTorch CUDA 12.8 (cu128) build şart**) veya Kaggle (haftada ~30 saat ücretsiz). Sprintte okul PC'si şart değil.

## 11. Görev dağılımı (öneri, ekip onayı bekleniyor)

| Kişi | Rol |
|---|---|
| Atay | Kod merkezi: repo, pertbench, veri pipeline'ı, tüm deneyler |
| Berk | MultiPert sorumlusu (mimari analizi, COVID'e uyarlama tasarımı) + hoca iletişimi |
| Alperen | Donör temsili literatürü (CellFlow, MultiCPA, CPA/biolord, scGen/scPILOT) + eşleşmesiz perturbation öğrenme (MMD/OT/flow) |
| Bengisu | Entegrasyon benchmark'ı (Fu vd.) + yöntem kartları (MIDAS, MultiVI, totalVI) + COVID veri yapısı |

## 12. 2 haftalık sprint (aktif plan)

**Kapsam:** Sadece hocanın 4 isteği: MultiPert'i anla, entegrasyonla geliştir, COVID verisi, görülmemiş donör. Nöroblastom, AML, genotip ve makale sprint dışında.

- **1. hafta (anla + hazırla):**
  - COVID verisini indir → incele → h5ad'e çevir.
  - LODO baseline tablosu.
  - MultiPert'i orijinal haliyle çalıştırıp delta metrikleriyle yeniden skorla.
  - Araştırma teslimleri: `multipert_mimari.md`, `donor_temsili.md`, `fu2025_kisa_liste.md`, `covid_veri_yapisi.md`.
  - Hafta sonu iç toplantı: 1 entegrasyon yöntemi + perturbation modülü tasarımı seçilir.
- **2. hafta (geliştir + sonuç):**
  - Seçilen entegrasyon yöntemini COVID'de çalıştır (batch = assay, donör değil).
  - Prototip: omurga latent'i + donör embedding'i + perturbation modülü, LODO 6 fold.
  - Karşılaştırma tablosu, `docs/sonuclar_sprint1.md`, 10 dk sunum.
  - **14. gün: hoca görüşmesi.**
- **Hocaya götürülecekler:**
  1. MultiPert analizi ve zayıf noktaları.
  2. COVID LODO baseline tablosu.
  3. En az 1 entegrasyon yönteminin COVID sonucu (donör korunuyor mu?).
  4. Geliştirilmiş MultiPert tasarımı + ilk prototip.
- **Ayrıntılı checklist:** `docs/Yapilacaklar_Sprint1.docx`. Plan: `docs/10_roadmap_gorev_paylasimi.md`.

## 13. Mevcut durum (1 Ekim 2026)

- **Yapıldı:**
  - Literatür taraması.
  - 3 verinin incelenmesi.
  - MultiPert ve MultiFlow kodlarının incelenmesi.
  - pertbench paketi (12 test geçiyor).
  - COVID scriptleri (sahte veriyle uçtan uca test edildi).
  - Repo.
  - Sprint planı ve dokümanlar.
- **Henüz yapılmadı:**
  - COVID verisi **indirilmedi** (Atay mobil veride; Wi-Fi bekleniyor).
  - MultiPert henüz **çalıştırılmadı** (PyTorch kurulumu Wi-Fi'da yapılacak).
  - Gerçek veride hiçbir entegrasyon yöntemi denenmedi.
- **Ön sonuçlar** (eski deneme verileri; COVID değil). Metrik `mse_top20`, düşük = iyi:

| Veri / görev | NoChange | PerturbationMean | ContextRidge (donör-farkında) |
|---|---|---|---|
| Sentetik (bilinçli donör etkisi), görülmemiş donör, RNA | 8,61 | 2,14 | **1,35** |
| Papalexi (THP-1), görülmemiş *replikat*, RNA | 0,361 | **0,039** | **0,039** |
| Papalexi, görülmemiş perturbation, RNA | 0,726 | 0,579 | **0,576** |

  Ders: Donör etkisi varsa donör-farkında model yakalıyor. Papalexi'de "donör" aslında replikat, bu yüzden kazanç yok. **Gerçek çok donörlü multimodal veri şart.**

## 14. Repo ve kod rehberi

```
pertbench/            Kendi benchmark paketimiz (pseudobulk düzeyinde)
  data.py             PerturbData (hücre), ConditionTable (koşul = perturbation × cell_type × donor),
                      pseudobulk(), pseudobulk_sparse(), merge_tables() (farklı hücrelerdeki assay'leri birleştirir)
  splits.py           random, unseen_perturbation, unseen_cell_type (LOO), unseen_donor (LOO, k_shot)
                      Kontroller her zaman eğitimde kalır.
  metrics.py          pearson_delta, pearson_delta_top20, mse_top20, direction_acc_top20, cosine_delta (+ ham pearson, referans)
  models.py           NoChange, GlobalMean, PerturbationMean, Additive, ContextKNN, ContextRidge,
                      LinearEmbedding (Ahlmann-Eltze tarzı), CrossModal
  external.py         export_split() + ExternalPredictions: harici modellerin (MultiPert vb.) tahminlerini aynı metrikle skorlar
  datasets.py         papalexi2021, frangieh2021_protein, covid_vaccine(files, donor_key, day_key, cell_type_key, control_day, …)
  synthetic.py        Bilinen donör × perturbation etkileşimli sentetik veri
scripts/covid/        00_check_env → 01_download → 02_inspect_rds → 03_convert → 04_run_lodo (--strict)
                      config.example.json: sütun adları 02 çıktısına göre doldurulur
scripts/              run_benchmark.py, download_data.py (scPerturb/Zenodo), build_docx.js, build_todo_docx.js
tests/                pytest (12 test)
docs/                 01–10 numaralı dokümanlar, PDF/docx çıktılar
research/             Ekip araştırma teslimleri (SABLON.md)
external/             MultiPert ve MultiFlow klonları (git'e dahil değil)
data/                 Veriler (git'e dahil değil)
```

**Kurulum:**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install git+https://github.com/cellgeni/py8rds.git
python -m pytest -q tests
```
- GPU'lu makinede: `pip install torch --index-url https://download.pytorch.org/whl/cu128`
- CPU'da: standart torch.

**Kodlama kuralları:**
- Mevcut stile uy.
- Test donörü hiçbir ön işleme adımına sızmamalı: HVG ve normalizasyon parametreleri sadece eğitim donörlerinden hesaplanır (`--strict`).
- Ham Pearson tek başına raporlanmaz; delta metrikleri esas alınır.

## 15. Açık sorular / riskler

- `py8rds` büyük Seurat dosyalarını (özellikle 4,7 GB ASAP) okuyabilecek mi? ASAP'ta ATAC assay'inin adı ne (`peaks`, `ATAC`, `GeneActivity`)?
- CITE ve ASAP hücre tipi etiketleri uyumlu mu?
- 6 donörle sonuçlar gürültülü olacak. Fold varyansı ve hücre tipi bazında raporlama gerekli.
- Aşı etkisi küçük alt popülasyonlarda; hücre tipi çözünürlüğü önemli.
- Ekip rol dağılımını henüz onaylamadı.
- Sprint sonrası (hocayla netleşecek): nöroblastomla asıl deney (diagonal entegrasyon, GLUE), ara rapor, donör temsilini WGS/genotiple zenginleştirmek.

## 16. Kaynaklar

- MultiPert: https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1014054 · https://github.com/MengyuanZhaoo/MultiPert
- MultiFlow: https://www.biorxiv.org/content/10.64898/2026.08.20.746112v1.full · https://github.com/liuq-lab/MultiFlow
- Fu vd. 2025 (Nat Methods, DOI 10.1038/s41592-025-02737-9); bioRxiv: https://www.biorxiv.org/content/10.1101/2025.04.01.646578v1.full
- Zhang vd. 2023: https://www.nature.com/articles/s41590-023-01608-9 · veri: https://zenodo.org/records/7555405
- Yu vd. 2025: https://www.nature.com/articles/s41588-025-02158-6 · https://pmc.ncbi.nlm.nih.gov/articles/PMC12081299
- Lambo vd. 2023: https://www.cell.com/cancer-cell/fulltext/S1535-6108(23)00364-1
- CellFlow: https://www.biorxiv.org/content/10.1101/2025.04.11.648220v1
- MultiCPA: https://www.biorxiv.org/content/10.1101/2022.07.08.499049v1
- totalVI: https://www.nature.com/articles/s41592-020-01050-x
- Ahlmann-Eltze vd. 2025 (derin modeller lineer baseline'ları geçemiyor): Nat Methods 22:1657
- scMultiBench (diğer entegrasyon benchmark'ı): https://www.nature.com/articles/s41592-025-02856-3
- py8rds: https://github.com/cellgeni/py8rds
