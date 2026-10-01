# 2 Haftalık Sprint: Roadmap ve Görev Paylaşımı

*1 Ekim 2026. Hedef: 2 hafta sonunda hocaya somut sonuçlarla gitmek.*

## Hocanın istedikleri (sprintin kapsamı)
1. **MultiPert'i iyice anlamak.**
2. **Multimodal entegrasyon yöntemleriyle (Fu vd. 2025) MultiPert'i geliştirmek.**
3. **COVID verisiyle başlamak** (Zhang vd. 2023: 6 donör, gün 0/2/10/28, CITE + ASAP).
4. Problem: **görülmemiş donörün** tedavi sonrası multimodal profilini, o donörün baseline hücrelerinden tahmin etmek.

Sprint dışı (sonraya): nöroblastom, AML, genotip, ablation'lar, makale.

## 2. haftanın sonunda hocaya götüreceklerimiz
1. **MultiPert analizi:** nasıl çalışıyor, nerede zayıf (eşleşme, split, metrik), bizim veriye neden doğrudan uymuyor.
2. **COVID verisi + ilk sonuçlar:** LODO baseline tablosu (6 fold).
3. **Entegrasyon:** kısa liste ve en az 1 yöntemin COVID'de çalıştırılmış hali (CITE + ASAP → ortak uzay, donör farkı korunuyor mu).
4. **Geliştirilmiş MultiPert önerisi:** entegrasyon omurgası + donör koşullu perturbation modülü. Tasarım + ilk prototip sonucu.

## Çalışma düzeni
- **Kod:** sadece Atay'ın PC'sinde. Repo: github.com/Atytmr07/perturbation-prediction (özel).
- **Araştırma:** Berk, Alperen, Bengisu kendi PC'lerinden, AI destekli. Teslimler `research/<isim>/<konu>.md`, şablon `research/SABLON.md`.
- **AI kuralı:** Her iddiaya birincil kaynak linki. Sayılar ve fonksiyon adları kaynaktan kontrol edilir. Emin olunmayan her şey "Açık sorular" bölümüne yazılır.
- **GPU** gerekirse Kaggle; okul PC'si sprintte şart değil.

## 1. hafta: anla + hazırla

| Gün | Atay (kod) | Berk | Alperen | Bengisu |
|---|---|---|---|---|
| 1–2 | Wi-Fi'da: COVID verisini indir, incele, h5ad'e çevir. CPU PyTorch kur | MultiPert makalesi + kodu: mimari, eğitim döngüsü, eşleşme, metrik | Donör temsili: CellFlow, MultiCPA (PoE), scGen/CPA. Görülmemiş donöre hangisi genellenir? | Fu vd. 2025: mosaic RNA+ADT / RNA+ATAC sonuçları. Python'daki adaylar: MIDAS, MultiVI, totalVI |
| 3–4 | LODO baseline'ları (`04_run_lodo.py --strict`). MultiPert'i orijinal haliyle çalıştır | **Teslim:** `multipert_mimari.md` | **Teslim:** `donor_temsili.md` | **Teslim:** `fu2025_kisa_liste.md`. Her aday için kurulum, girdi formatı, batch ayarı, örnek kod |
| 5 | MultiPert tahminlerini delta metrikleriyle yeniden skorla | MultiPert'in COVID'e uyarlama tasarımı (eşleşme yok, modaliteler ayrı hücrede) | Eşleşmesiz perturbation öğrenme: MMD/OT kaybı, 6 donörde ne mantıklı | COVID verisinin yapısı: hücre tipleri, CITE–ASAP hücre tipi eşlemesi, gün etkisi nerede büyük |
| 6–7 | **İç toplantı (30 dk):** herkes 5 dk anlatır. Entegrasyon için 1 yöntem ve perturbation modülü tasarımı seçilir | | | |

**1. hafta sonu çıktıları:** COVID verisi hazır, LODO baseline tablosu, MultiPert yeniden skorlanmış, 3 araştırma dosyası, seçilmiş omurga + modül.

## 2. hafta: geliştir + sonuç

| Gün | Atay (kod) | Berk | Alperen | Bengisu |
|---|---|---|---|---|
| 8–9 | Seçilen entegrasyon yöntemini COVID'de çalıştır (CITE + ASAP, köprü ADT, **donör batch olarak verilmez**) | Geliştirilmiş MultiPert'in sözde kodu: omurga latent'i + donör embedding'i + MultiPert'in dikkat bloğu | Değerlendirme: donör korunumu metriği, latent'te MMD; pertbench'e eklenecek tanımlar | Seçilen yöntemin uygulama kartını kesinleştir. Çalıştırmada çıkan hatalara destek |
| 10–11 | Prototip: entegrasyon latent'i üzerinde donör koşullu perturbation modülü; LODO 6 fold | Prototip sonuçlarını MultiPert ve baseline'larla karşılaştıran tablo | Hata analizi: hangi hücre tipi/günde başarısız | Sunum için şekiller: veri yapısı, mimari şeması |
| 12–13 | Sonuçları sabitle, `docs/sonuclar_sprint1.md` | Sunum (10 dk) | Sunum: yöntem kısmı | Sunum: veri + entegrasyon kısmı |
| 14 | **Hoca görüşmesi** | | | |

## Riskler ve B planları
| Risk | B planı |
|---|---|
| py8rds Seurat dosyalarını okuyamaz | `readseurat`; o da olmazsa Colab'de tek seferlik dönüşüm |
| Entegrasyon yöntemi CPU'da çok yavaş | Kaggle GPU; ya da hücreleri alt örnekle (donör × gün × hücre tipi başına sabit sayı) |
| Prototip 2. haftada yetişmez | Hocaya tasarım + baseline + entegrasyon sonucuyla git, prototipi bir sonraki görüşmeye bırak |
| 6 donörle sonuçlar gürültülü | Fold'lar arası varyansı göster. Sonuçları hücre tipi ve gün bazında raporla |

## Sprint sonrası (hocayla birlikte netleşecek)
Nöroblastom (22 hasta) ile asıl deney, ara rapor, model geliştirme, final.
