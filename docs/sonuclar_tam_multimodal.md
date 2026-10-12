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

---

## Ek: ATAC'ta aşıya özgü bölgeler, 12 Ekim 2026
**Deneme:** ATAC'ta en değişken 20 bin peak yerine, veri setiyle gelen `antigen_module_peaks.rds` kullanıldı (2.678 peak; makalede aşıya özgü CD8 T hücrelerinde açılan bölgeler). Yükleyiciye `features` seçeneği eklendi (`data/covid/antigen_module_peaks.txt`).
- Konfigürasyonlar: `scripts/covid/config_antigen_peaks_l1.json`, `config_antigen_peaks_l2.json`
- Sonuçlar: `results/covid_lodo_antigen_peaks_{l1,l2}/`, `results/covid_signal_noise_antigen_peaks_{l1,l2}.csv`
- ⚠ Bu peak listesi makalede **tüm donörlerle** belirlendi. Görülmemiş donör testi açısından hafif bir sızıntı taşıyor.

| | ATAC pearson_δ (PerturbationMean) | ATAC mse_top20: NoChange / PerturbationMean | Ortak etki / gürültü (medyan) |
|---|---|---|---|
| En değişken 20 bin peak, l1 | 0,020 | 0,071 / 0,071 | ~0,20 |
| **Aşıya özgü 2.678 peak, l1** | 0,038 | 0,027 / 0,027 | 0,21–0,27. T hücrelerinde 11. ve 28. gün **0,29–0,40**; CD8 T'de donöre özgü pay %51–69 |
| Aşıya özgü 2.678 peak, l2 | 0,018 | 0,042 / 0,042 | 0,20–0,27 (CD8 TEM'de bile ≤ 0,3) |

**Sonuç:** Aşıya özgü bölgeler, T hücrelerinde sinyali yaklaşık iki katına çıkarıyor, ama sinyal hâlâ gürültünün altında. Hiçbir model "değişim yok" tahminini geçemiyor.

### Neden? Etki nadir bir hücre grubunda yoğunlaşıyor ve donöre çok bağlı
Hücre başına makale skorları (`antigen_module_score`: CITE/RNA, `GA_antigen_score`: ASAP/ATAC). CD8 T içinde, skoru gün 0 CD8 T'lerinin %95'lik eşiğinin üstünde olan hücrelerin oranı:

| Donör | RNA modülü (gün 0 → 2 → 11 → 28) | ATAC modülü (gün 0 → 28) |
|---|---|---|
| donorJ | 8,0 → 12,9 → 9,6 → **33,3** | 5,7 → **11,8** |
| donorF | 4,8 → 7,7 → 4,3 → **12,6** | 5,1 → 3,5 |
| donorA | 0,5 → 1,1 → 0,2 → 3,9 | 1,8 → 2,3 |
| donorM | 9,6 → 14,6 → 6,4 → 3,3 | 10,5 → 7,6 |
| donorB | 5,7 → 4,4 → 0,4 → 1,9 | 6,1 → 3,5 |
| donorE | 4,3 → 6,5 → 1,7 → 0,3 | 3,8 → 4,0 |

**Yorum:**
1. 28. günde aşıya cevap veren CD8 T oranı donörler arasında **%0,3 ile %33** arasında değişiyor. Bu, verideki en güçlü donöre özgü sinyal.
2. Bu sinyal küçük bir alt popülasyonda olduğu için, hücre tipi ortalamasında (pseudobulk) seyreliyor. ATAC'ta sinyal çıkmamasının ana nedeni bu.
3. ATAC modülünde artış sadece en güçlü cevap veren donörde (donorJ) görülüyor.

**Öneri:** Donör sorusu için hedefi, ortalama profil yerine **"aşıya cevap veren hücre oranı"** gibi bir alt popülasyon ölçüsüne kaydırmak. Soru şu olur: "Donörün gün 0 hücrelerinden, gün 28'de ne kadar güçlü bir antijen-spesifik T hücre cevabı oluşacağını tahmin edebilir miyiz?" Bu hem biyolojik olarak anlamlı, hem de verideki asıl donör farkını hedefliyor. 6 donörle istatistiksel güç çok düşük, bu yüzden bu ilk aşamada betimsel bir bulgu.
