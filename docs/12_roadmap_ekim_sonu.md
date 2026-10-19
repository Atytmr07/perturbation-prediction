# Ortak Roadmap: 20 Ekim – 9 Kasım 2026

*19 Ekim 2026. `docs/11_ortak_roadmap.md`'nin yerine geçer. Eski takvim yaklaşık bir hafta kaydı.*

## Durum (19 Ekim)
- **MultiPert:** Yeniden üretildi (RNA PCC 0,78, protein 0,79). Tahminler neredeyse sabit; değişim tabanlı metriklerle basit ortalamayı geçemiyor. Bengisu'nun makale notları `research/bengisu/` altında.
- **COVID:** RNA + protein + ATAC dönüştürüldü. 6 fold LODO, 8 ana tip ve 26–30 ince tip. Sonuçlar `results/LEADERBOARD.md`.
  - RNA'da en iyi tahmin "diğer donörlerin ortalaması".
  - Protein ve ATAC'ta hiçbir model "değişim yok" tahmininden iyi değil.
- **ATAC:** En değişken peak'lerle de, makalenin aşıya özgü 2.678 peak'iyle de etki gürültünün altında.
- **Ana bulgu:** Aşının etkisi nadir bir hücre grubunda yoğunlaşıyor ve donöre çok bağlı. Gün 28'de aşıya cevap veren CD8 T oranı donörler arasında %0,3–33. Ayrıntı: `docs/sonuclar_tam_multimodal.md`.
- **Başlamayanlar:** MultiPert'in COVID uyarlaması, MultiVI, MIDAS/totalVI. 12 Ekim'den beri ekipten yeni teslim yok.

## İş paketleri
Herkes bir paket üstlenir; sorumlular toplantıda belirlenir.

| Hafta | Paket | İş | Çıktı |
|---|---|---|---|
| 1 (20–26 Ekim) | **P1 – Hoca görüşmesi** | Sunum: MultiPert analizi, COVID tabloları, alt popülasyon bulgusu. Yön kararı | `docs/` altında karar notu |
| 1 | **P2 – MultiPert / COVID** | CITE (RNA + protein aynı hücrede) üzerinde: donör bazlı bölme, gün 0 hücrelerinin aynı donör ve hücre tipinden eşlenmesi, LODO 6 fold | LEADERBOARD'da MultiPert satırı |
| 1–2 | **P3 – MultiVI** | CITE + ASAP, köprü protein, batch = assay (**donör değil**). Ölçülecekler: modalite hizalama, donör korunumu, aşıya cevap veren hücrelerin iki assay'de eşleşmesi | `results/integration/` + kısa rapor |
| 2 (27 Ekim – 2 Kasım) | **P4 – Alt popülasyon hedefi** | Hedef: gün 0'dan, gün 28'deki antijen-spesifik CD8 T oranını tahmin etmek. Eşik sadece eğitim donörlerinden belirlenir. 6 donörle sonuç betimsel kalır | Yeni hedefin LODO tablosu |
| 3 (3–9 Kasım) | **P5 – Nöroblastom** | Yu vd. 2025: 22 hasta, kemoterapi öncesi/sonrası. HTAN / CELLxGENE erişimi, aynı pipeline. Hedef adayı: mezenkimal (dirençli) alt tip oranı | Veri hazır + ilk tablo |

## Hocaya sorulacaklar
1. Hedefi "tüm profil" yerine alt popülasyon ölçüsüne kaydıralım mı?
2. 6 donör az. Nöroblastoma ne zaman geçelim?
3. Entegrasyon için öncelik MultiVI mi, MIDAS mı?

## Kurallar (değişmedi)
- Aynı veri, aynı değerlendirme (`pertbench`, `--strict`). Çıta: `PerturbationMean`.
- Sonuçlar `results/LEADERBOARD.md`'ye, notlar `research/<isim>/`'e. WhatsApp'ta kalan bilgi kaybolur.
- AI kullanırken her iddiaya kaynak; sayılar kaynaktan kontrol edilir.
- Hesaplama: bu PC (CPU) veya Kaggle (GPU).
