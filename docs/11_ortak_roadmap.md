# Ortak Roadmap (5 Ekim 2026)

**Çalışma şekli:** Herkes farklı bir yaklaşım dener. Hepsi **aynı veri + aynı değerlendirme** ile ölçülür ve tek bir sonuç tablosuna (leaderboard) yazılır. En iyi sonucu veren yaklaşımın üzerine eklemeler yapılır.

## Hocanın istekleri ve durum

| # | Hocanın isteği | Durum | Kalan iş |
|---|---|---|---|
| 1 | **MultiPert'i iyice anlamak** | Kod incelendi, çalıştırıldı, makaledeki sonuçlar yeniden üretildi (Atay, CPU). Bulgu: tahminler neredeyse sabit; delta metrikleriyle basit ortalamayı geçemiyor | Methods/mimari özeti (`research/…/multipert_mimari.md`). Bengisu'nun GPU çalıştırmasıyla farkın kaynağı (tek test: Atay'ın ön işlenmiş dosyalarıyla eğitim) |
| 2 | **Entegrasyon yöntemleriyle (Fu vd. 2025) MultiPert'i geliştirmek** | Aday yöntemler belirlendi (MultiVI, totalVI, MIDAS, GLUE). scvi-tools kurulu | Adayları COVID'de denemek → bu roadmap'in ana işi |
| 3 | **COVID verisiyle başlamak** (+ görülmemiş donör sorusu) | Veri indirildi. CITE (RNA + protein) dönüştürüldü. İlk LODO tablosu ve sinyal/gürültü analizi çıktı | ASAP (ATAC + protein) dönüşümü, tam multimodal tablo |

## Ortak kurallar (herkes için)
1. **Veri:** Herkes aynı h5ad dosyalarını kullanır (Atay hazırlar, Drive'a koyar). Kimse kendi ön işlemesini yapmaz. Yapacaksa leaderboard'da ayrıca belirtir.
2. **Değerlendirme:** Leave-one-donor-out, 6 fold. Test donörünün sadece gün 0 hücreleri görülebilir. Özellik seçimi ve normalizasyon sadece eğitim donörlerinden yapılır.
3. **Teslim formatı:** Her model, tahminlerini tek bir CSV olarak verir. Sütunlar: `perturbation, cell_type, donor, modality, <özellik adları>`. Satırlar donör × gün × hücre tipi düzeyinde ortalama profil. Atay bu CSV'yi `pertbench` ile skorlar; böylece herkes aynı kodla ölçülür.
4. **Çıta:** `PerturbationMean`, yani diğer donörlerin ortalama değişimi. Bunu geçmeyen sonuç "iyileşme" sayılmaz.
5. **Seed:** En az 3 seed. Tek seed'lik sonuç "ön sonuç" diye işaretlenir.
6. **Kayıt:** Her deney `research/<isim>/` altına kısa bir md dosyasıyla girer: ne denendi, ayarlar, sonuç, sorunlar.
7. **Zaman noktaları:** gün 0 / 2 / **11** / 28. Eski dokümanlarda "gün 10" yazıyor, yanlış.

## Denenecek yaklaşımlar (her biri bir kişinin sorumluluğunda)

| İz | Yaklaşım | Neden | Sorumlu (öneri) |
|---|---|---|---|
| **A** | **MultiPert'i COVID'e uyarlamak:** CITE'ta RNA ve protein aynı hücrede ölçüldüğü için MultiPert burada doğrudan çalışabilir. Değişiklikler: kontrol (gün 0) hücreleri aynı donör ve hücre tipinden eşlenir, split donör bazlı yapılır | Hocanın 1. ve 2. maddesinin doğrudan karşılığı. "MultiPert görülmemiş donörde ne yapıyor?" sorusunu cevaplar | Berk |
| **B** | **MultiVI ile entegrasyon:** CITE + ASAP aynı latent uzaya taşınır, köprü protein. Perturbation latent uzayda tahmin edilir (önce basit: latent'te PerturbationMean/ridge), sonra RNA, ATAC ve proteine geri decode edilir | RNA + ATAC'ı birlikte ele alan tek iz. Hocanın problem tanımına en yakın olanı | Alperen |
| **C** | **Fu vd.'den ikinci aday:** MIDAS (mosaic'te Fu vd.'nin en iyisi) veya totalVI (sadece CITE, RNA + protein). B ile aynı latent tahmin adımı | B'ye karşı kontrol. Hangi entegrasyon omurgası daha iyi? | Bengisu |
| **0** | **Altyapı + baseline'lar:** Veri hazırlama, ASAP dönüşümü, ortak h5ad'ler, LODO skorlama, leaderboard. Ayrıca donör-farkında baseline'lar | Herkesin aynı şekilde ölçülmesini sağlar | Atay |

İz A ve B/C, "entegrasyonla geliştirilmiş MultiPert" fikrinin iki yarısı:
- **A:** MultiPert'in perturbation modülü bizim kurguda ne kadar işe yarıyor?
- **B/C:** Hangi entegrasyon omurgası daha iyi?

İkinci haftada en iyi modül + en iyi omurga birleştirilir.

## Takvim

| Zaman | İş | Çıktı |
|---|---|---|
| **6–8 Ekim** | Atay: ASAP dönüşümü + ortak h5ad'ler (Drive) + tam multimodal LODO baseline tablosu + leaderboard dosyası. Diğerleri: yaklaşımlarını okuyup kurulumu hazırlar | `results/LEADERBOARD.md` ilk satırlar (baseline'lar) |
| **9–12 Ekim** | Her iz ilk versiyonunu çalıştırır (tek seed), CSV'yi teslim eder, Atay skorlar | Leaderboard'da A, B, C satırları |
| **12 Ekim** | **İç toplantı (30 dk):** Tabloya bakılır. En iyi yaklaşım seçilir; diğerlerinden hangi parça alınabilir? | Karar notu |
| **13–17 Ekim** | Seçilen yaklaşım geliştirilir (ör. en iyi omurga + MultiPert modülü + donör bilgisi). 3 seed, basit istatistik (fold bazında eşli test). Herkes bir parçasını üstlenir | Leaderboard'da birleşik model |
| **18–19 Ekim** | Sonuç notu (`docs/sonuclar_sprint1.md`) + 10 dk sunum | Sunum |
| **~20 Ekim** | **Hoca görüşmesi** | |

## Hocaya götürülecekler
1. MultiPert analizi: yeniden üretim, neredeyse sabit tahmin, metrik sorunu.
2. COVID'de görülmemiş donör tablosu: baseline'lar + A, B, C + birleşik model.
3. Donöre özgü sinyal analizi: tahmin edilecek bir sinyal var mı?
4. Hangi entegrasyon yönteminin daha iyi çalıştığı ve bir sonraki adım önerisi.
