# Roadmap ve Görev Paylaşımı

*1 Ekim 2026*

## Çalışma düzeni
| Rol | Nerede | Ne yapar |
|---|---|---|
| **Kod merkezi** (Atay'ın PC'si: 64 GB RAM, CPU) | Bu makine | Tüm kod, veri işleme ve deneyler burada. Sonuçlar repoya yazılır |
| **Araştırma** (Berk, Alperen, Bengisu) | Kendi PC'leri + AI araçları | Okuma, yöntem araştırması, tasarım. Çıktılar kod merkezinin doğrudan uygulayabileceği formatta teslim edilir |
| **GPU** (sonra) | Okul PC'si (RTX 5070) / Kaggle | Büyük modellerin eğitimi. Aynı repo ve scriptlerle |

**Teslim kuralı:** Her araştırma çıktısı repoda `research/<isim>/<konu>.md` olarak durur ve aşağıdaki şablonu izler. Kod merkezi sadece bu dosyalardan iş alır. WhatsApp'ta kalan bilgi kaybolur.

```
# <Konu>
## Özet (5 satır)
## Bulgular (her biri birincil kaynak linkiyle)
## Uygulama bilgisi: kurulum, girdi formatı, çıktı, GPU/RAM ihtiyacı, örnek kod
## Bizim projeye önerisi: ne yapalım, neden
## Kod merkezine iş: çalıştırılacak somut adımlar
## Açık sorular / emin olmadıklarım
```

**AI ile araştırma kuralları:**
1. Her iddia için birincil kaynak linki (makale, GitHub, dokümantasyon) zorunlu. "AI söyledi" kaynak değildir.
2. Sayılar (hücre sayısı, skor, parametre) kaynaktan kontrol edilir. AI'ın uydurduğu sayı ve atıf çok sık oluyor.
3. Kod örnekleri resmi dokümantasyondan alınır. Fonksiyon adları ve parametreler, kütüphanenin güncel versiyonunda var mı diye kontrol edilir.
4. Emin olunmayan her şey "Açık sorular" bölümüne yazılır, bulgu gibi sunulmaz.

---

## Roadmap

### Faz 0: Hazırlık (bu hafta; veri indirmeden)
**Hedef:** Herkes problemi ve iki izi anlamış olsun. Kod tarafı veri gelmeden hazır olsun.

| Kim | Görev | Çıktı |
|---|---|---|
| Atay | GitHub reposunu kur, herkese erişim ver | Özel repo |
| Atay | pertbench'e **dağılım metrikleri** ekle (MMD, energy distance; sentetik veriyle test) | Kod + test |
| Atay | MultiPert'in **donör bazlı bölme + donör içi eşleşme** versiyonunu kendi kopyamızda yaz, sentetik veriyle test et (PyTorch kurulumu Wi-Fi'da) | `models/multipert_lodo/` |
| Berk | MultiPert derin okuma (makale + kod, AI yardımıyla) | `research/berk/multipert_mimari.md` |
| Alperen | Donör temsili ve perturbation modülü literatürü | `research/alperen/donor_temsili.md` |
| Bengisu | Fu vd. 2025 benchmark'ı + mosaic yöntem kısa listesi | `research/bengisu/fu2025_kisa_liste.md` |
| Hepsi | Hafta sonu iç toplantı (30 dk) | Kararlar → `docs/` |

### Faz 1: COVID verisi ve ilk sayılar (2. hafta)
**Hedef:** Gerçek veride ilk LODO tablosu.

| Kim | Görev | Çıktı |
|---|---|---|
| Atay | Veriyi indir, incele, dönüştür (`scripts/covid/01–03`) | h5ad + veri özeti tablosu |
| Atay | LODO baseline'ları (`04_run_lodo.py --strict`) | `results/covid_lodo/` |
| Atay | MultiPert'i orijinal haliyle çalıştır, delta metrikleriyle yeniden skorla | Karşılaştırma tablosu |
| Bengisu | COVID verisinin yapısını yorumla: hücre tipleri, gün etkisi hangi hücrede büyük, CITE–ASAP hücre tipi eşlemesi | `research/bengisu/covid_veri_yapisi.md` |
| Berk | MultiPert'in COVID'e uyarlama tasarımı: eşleşme yok, modaliteler ayrı hücrede | `research/berk/multipert_uyarlama.md` |
| Alperen | Dağılım düzeyinde perturbation modülleri: OT, flow matching, CellFlow tarzı koşullama. Hangisi küçük veride (6 donör) mantıklı? | `research/alperen/dagilim_modulleri.md` |

### Faz 2: Entegrasyon omurgası (3.–4. hafta)
**Hedef:** COVID'de CITE + ASAP'ı ortak uzaya taşıyan ve donör farkını koruyan bir omurga seçmek.

| Kim | Görev | Çıktı |
|---|---|---|
| Bengisu | Kısa listedeki her yöntem için uygulama kartı: MIDAS, MultiVI, GLUE, totalVI. Kurulum, girdi, batch ayarı, örnek kod | `research/bengisu/yontem_kartlari.md` |
| Atay | Kartlara göre yöntemleri çalıştır (küçükse CPU, büyükse Kaggle/okul PC'si) | Embedding'ler + metrik tablosu |
| Atay | Değerlendirme: Fu vd. metrikleri + **donör korunumu** + modaliteler arası imputasyon | `results/integration/` |
| Berk + Alperen | Seçilecek omurganın üstüne perturbation modülünün **tasarım dokümanı**: girdiler, kayıp fonksiyonu, eğitim döngüsü, sözde kod | `research/ortak/model_tasarimi_v1.md` |
| Hepsi | **Hoca görüşmesi:** ilk LODO tablosu, MultiPert yeniden skorlama, entegrasyon karşılaştırması, mimari önerisi | Sunum |

### Faz 3: Model v1 (5.–7. hafta)
**Hedef:** Omurga + donör koşullu perturbation modülü. COVID'de LODO ile baseline'ları geçiyor mu?

| Kim | Görev |
|---|---|
| Atay | Model v1'i tasarım dokümanına göre kodla. Eğitim okul PC'sinde/Kaggle'da |
| Berk | Ablation planı: donör embedding var/yok, omurga A/B, modalite var/yok |
| Alperen | Hata analizi: hangi hücre tipi ve hangi günde model başarısız, neden |
| Bengisu | Nöroblastom verisine erişim: HTAN / CELLxGENE, hangi kısımlar açık, nasıl indirilir |

### Faz 4: Nöroblastom (8.–10. hafta, ~Aralık)
**Hedef:** Probleme en birebir uyan veride (22 hasta, kemoterapi öncesi/sonrası) asıl deney.

- Diagonal entegrasyon (GLUE; RNA ve ATAC tamamen ayrı hücrelerde).
- LODO, 22 fold.
- **Ara rapor** (CS4001 teslimine göre).

### Faz 5: Geliştirme (Ocak–Mart)
- Donör temsilini zenginleştirmek: WGS / genotip (nöroblastomda var), baseline dağılımı için set encoder.
- AML verisi (opsiyonel) ile genelleme testi.
- Gerekirse MultiPert dışında güçlü bir alternatif modülle karşılaştırma.

### Faz 6: Final (Nisan–Haziran)
- Son deneyler, istatistiksel testler, şekiller.
- Tez/rapor yazımı. Mümkünse workshop veya bioRxiv.

---

## Kişi bazında görev kartları (Faz 0–1)

### Atay: kod merkezi
- Repo, ortam, pertbench, veri pipeline'ı, tüm deneylerin çalıştırılması.
- Araştırma dosyalarını koda çevirmek. Belirsizlik varsa dosyanın "Açık sorular" bölümüne not düşmek.
- Haftalık "sonuçlar" notu: `docs/sonuclar_haftaN.md`.

### Berk: MultiPert sorumlusu + hoca iletişimi
**Araştırma soruları:**
1. MultiPert'in her bloğu (ZINB-VAE, AE, shared encoder, fusion, dual attention, decoder, discriminator) ne yapıyor? Girdi/çıktı boyutları neler?
2. Eğitim döngüsünde generator ve discriminator hangi sırayla güncelleniyor, kayıplar nasıl toplanıyor?
3. Kontrol hücreleri ve perturbe hücreler nasıl eşleşiyor? Bu eşleşme kaldırılırsa (bizim verilerde eşleşme yok) model nasıl eğitilir?
4. Donör bilgisi modele hangi noktadan en doğal şekilde girer?
5. Makaledeki metrikler neden iyimser? Bizim delta metrikleriyle ne beklenir?

**AI'a örnek istem:** *"github.com/MengyuanZhaoo/MultiPert reposundaki code/models.py ve code/trainer.py dosyalarını açıkla. Her sınıfın girdi/çıktı tensör boyutlarını ve eğitim döngüsünde kayıpların nasıl hesaplandığını satır referanslarıyla anlat."* Kodu AI'a yapıştırarak sormak daha güvenilir sonuç verir.

**Teslim:** `multipert_mimari.md` (Faz 0), `multipert_uyarlama.md` (Faz 1).

### Alperen: donör temsili + perturbation modülü
**Araştırma soruları:**
1. Mevcut yöntemler donörü/hastayı nasıl temsil ediyor? CellFlow (kontrol ortalaması), CPA/biolord (kategorik kovaryat), scGen/scPILOT (latent aritmetik / OT transfer). Hangisi **görülmemiş** donöre genellenebilir?
2. MultiCPA'nın Product of Experts birleştirmesi nasıl çalışıyor? Eksik modaliteyi nasıl ele alıyor?
3. Hücre eşleşmesi olmadan (öncesi ve sonrası farklı hücreler) perturbation nasıl öğrenilir? OT, flow matching, MMD kaybı. Sadece 6 donör varken hangisi mantıklı?
4. Dağılım düzeyinde başarı nasıl ölçülür? (MMD, energy distance, Wasserstein; pseudobulk delta'ya ek olarak.)

**AI'a örnek istem:** *"CellFlow (Klein et al., bioRxiv 2025.04.11.648220) makalesinde donör bilgisi modele nasıl veriliyor ve görülmemiş donör deneyi nasıl kurulmuş? Methods bölümünden alıntı ve sayfa/bölüm referansıyla açıkla."*

**Teslim:** `donor_temsili.md` (Faz 0), `dagilim_modulleri.md` (Faz 1).

### Bengisu: entegrasyon benchmark'ı + veri
**Araştırma soruları:**
1. Fu vd. 2025: mosaic (RNA+ADT, RNA+ATAC) ve diagonal kategorilerinde hangi yöntemler önde, hangi metrikle? Supplementary'de yöntem ayarları neler?
2. Python'da çalışan adaylar (MIDAS, MultiVI, GLUE, totalVI): kurulum, girdi formatı (h5ad/MuData), batch nasıl veriliyor, GPU/RAM ihtiyacı, örnek kod.
3. Bu yöntemlerden hangisi **iki assay arasında köprü modalite (ADT)** senaryosunu, yani bizim COVID verimizi doğrudan destekliyor?
4. Fu vd.'nin metrik paketi ve pipeline'ı nerede, nasıl kullanılıyor?
5. (Faz 1) COVID verisinin yapısı: hücre tipleri, gün etkisi, CITE–ASAP hücre tipi eşlemesi.

**AI'a örnek istem:** *"MIDAS (He et al., Nat Biotech 2024) ile CITE-seq (RNA+ADT) ve ASAP-seq (ATAC+ADT) verilerini ADT üzerinden mosaic olarak birleştirmek için resmi dokümantasyondaki kurulum ve kullanım adımlarını, girdi dosya formatıyla birlikte ver. Kaynak linklerini ekle."*

**Teslim:** `fu2025_kisa_liste.md` (Faz 0), `covid_veri_yapisi.md` (Faz 1), `yontem_kartlari.md` (Faz 2).

---

## Kilometre taşları
| Zaman | Kilometre taşı |
|---|---|
| Faz 0 sonu | Herkesin ilk araştırma dosyası repoda. Repo + ortam hazır |
| Faz 1 sonu | COVID LODO baseline tablosu. MultiPert'in yeniden skorlanmış hali |
| Faz 2 sonu | Omurga seçildi. **Hoca görüşmesi** |
| Faz 3 sonu | Model v1, COVID'de LODO sonuçları |
| Faz 4 sonu | Nöroblastom sonuçları. **Ara rapor** |
| Haziran | Final rapor |
