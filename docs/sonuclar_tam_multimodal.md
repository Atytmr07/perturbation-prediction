# Tam Multimodal LODO Sonuçları (7 Ekim 2026)

## Ne yapıldı
- **ASAP dönüştürüldü** (R'sız, `py8rds`): ATAC 78.677 hücre × 118.137 peak (ham sayımlar), protein 175 marker.
  - `py8rds`'in Seurat dönüştürücüsü ADT'nin özellik metadata'sında hata verdi. `03_convert.py`'ye bu adımı atlayan bir yedek okuma yolu eklendi.
  - **ASAP'taki ADT katmanının adı `scale.data`, ama içinde ham sayımlar var.** Değerlerin hepsi tam sayı ve hücre toplamları `nCount_ADT` ile birebir aynı. Bu yüzden CITE proteini gibi CLR ile normalize edildi.
  - Hücre tipi etiketleri: CITE'ta `celltypel1`, ASAP'ta `predicted.CITE_l1` (CITE'tan aktarılmış).
- **Yükleyici güncellendi:** tablo bazında hücre tipi sütunu ve normalizasyon seçilebiliyor.
- **Değerlendirme kodu güncellendi:** Kontrolü (gün 0) olmayan test koşulları atlanıp raporlanıyor. Nadir hücre tiplerinde gün 0 grubu bir assay'de 10 hücrenin altında kalabiliyor; 9 koşul bu yüzden atlandı.
- Testler: 15/15 geçiyor.

## Sonuç tablosu
Ayrıntı: `results/LEADERBOARD.md`. Değerler top-20 MSE (düşük = iyi), 6 fold, `--strict`.

| Modalite | NoChange | PerturbationMean | En iyi diğer |
|---|---|---|---|
| RNA | 0,203 | **0,165** | CrossModal 0,165 (eşit) · ContextRidge pearson_δ'da biraz önde (0,287'ye karşı 0,278) |
| CITE protein | 0,059 | 0,059 | Additive 0,058 |
| **ATAC** | **0,071** | 0,071 | Hepsi ≈ NoChange (pearson_δ ~0,02) |
| ASAP protein | 0,033 | 0,031 | CrossModal 0,030 |

## Sinyal/gürültü (`results/covid_signal_noise_full.csv`)
Hücre tipi l1. Değerler gün bazında medyan.

| Modalite | Ortak etki / gürültü | Donöre özgü pay (gürültü düşülmüş) |
|---|---|---|
| RNA | 0,6–1,4 | %40–72 |
| Protein (iki assay birlikte) | 0,4–0,8 | %49–68 |
| **ATAC** | **~0,2** | **%0** |

## Yorum
1. **RNA ve protein:** Önceki sonuç değişmedi. "Diğer donörlerin ortalaması" (`PerturbationMean`) en iyi ya da en iyiye eşit. Donöre özgü bir sinyal var, ama basit donör-farkında modeller onu tahmin edemiyor.
2. **ATAC'ta, bu çözünürlükte, aşı etkisi görünmüyor.** Ana hücre tipi düzeyinde ve en değişken 20 bin peak'te, ortak etki ölçüm gürültüsünün yaklaşık beşte biri. Hiçbir model "değişim yok" tahmininden iyi değil. Olası nedenler:
   - Etki küçük alt popülasyonlarda (antijene özgü CD8 T) yoğunlaşıyor ve 8 ana tip içinde seyreliyor.
   - Peak düzeyindeki veri çok seyrek.
   - En değişken peak'ler aşıya cevap veren peak'ler değil.
3. **Projeye etkisi:** Hocanın sorusunun ATAC tarafı, bu veride ana hücre tipi düzeyinde test edilemiyor. Sonraki denemeler:
   - (a) İnce hücre tipleri (l2: 26–30 tip; l3).
   - (b) Peak yerine gene activity veya motif skorları (chromVAR tarzı).
   - (c) Aşıya cevap veren bölgeler: veri setinde `antigen_module_peaks.rds` var.
   - (d) Entegrasyon omurgası (MultiVI): ATAC'ı RNA ve proteinle ortak uzaya taşıyıp latent'te karşılaştırmak.

## Not
Tam tablo, iki assay'de de yeterli hücresi olan koşulları kullandığı için (176 koşul), sadece CITE ile çalışan önceki tablodan (192 koşul) farklı bir koşul kümesine sahip. Bu yüzden RNA sayıları iki tablo arasında doğrudan karşılaştırılamaz.

---

## Ek: İnce hücre tipleri (l2), 12 Ekim 2026
26–30 alt tip; 384 koşul, 263 test koşulu. Ayrıntı: `results/LEADERBOARD.md`, `results/covid_lodo_full_l2/`, `results/covid_signal_noise_full_l2.csv`.

| Modalite | NoChange | PerturbationMean | Not |
|---|---|---|---|
| RNA | 0,240 | **0,205** | ContextRidge pearson_δ'da önde (0,231 / 0,211), ama MSE'de geride. Koşulların sadece %35'inde çıtayı geçiyor |
| CITE protein | **0,068** | 0,070 | Değişim yok tahmini en iyi |
| ATAC | **0,107** | 0,109 | Değişim yok tahmini en iyi |
| ASAP protein | **0,040** | 0,042 | Değişim yok tahmini en iyi |

**Sinyal/gürültü (l2, gün bazında medyan):**
- RNA: ortak etki / gürültü 0,36–0,71; donöre özgü pay %33–65.
- Protein: 0,32–0,56; donöre özgü pay %38–61.
- **ATAC: 0,19–0,22; donöre özgü pay %0.** En iyi alt tipte bile (B intermediate, CD14 Mono; gün 2) ortak etki / gürültü ≤ 0,35.

**Yorum:**
1. İnce hücre tiplerine inmek sonucu değiştirmedi. Hücre başına sayı azaldığı için gürültü arttı; proteinde artık "değişim yok" tahmini bile en iyi.
2. **ATAC'ta aşı etkisi, en değişken 20 bin peak ile pseudobulk düzeyinde hiçbir hücre tipinde görünmüyor.** Bir sonraki deneme peak seçimiyle ilgili olmalı:
   - (a) Veri setindeki aşıya cevap veren bölgeler (`antigen_module_peaks.rds`).
   - (b) Peak'leri genlere toplayan gene activity skorları.
   - (c) Motif / chromVAR tarzı skorlar.
3. RNA'da donör-farkında modeller hâlâ çıtayı geçemiyor. Asıl test, entegrasyon omurgası (MultiVI) ve MultiPert'in COVID uyarlaması olacak (roadmap B ve A izleri).
