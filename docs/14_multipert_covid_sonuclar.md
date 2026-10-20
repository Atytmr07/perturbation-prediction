# MultiPert COVID Uyarlaması: Sonuçlar ve Bengisu'nun Analiziyle Karşılaştırma (20 Ekim 2026)

Roadmap paketi **P2** (`docs/12_roadmap_ekim_sonu.md`). Aynı soru iki ayrı pipeline'la, birbirinden bağımsız test edildi:

- **Atay:** `scripts/multipert/03_covid_lodo.py`. pertbench metrikleriyle değerlendirildi.
- **Bengisu:** `docs/13_multipert_covid_diagnostics.md`, `scripts/multipert/04–05`. Fork'u `bengssy/perturbation-prediction` (`multipert-covid-diagnostics` dalı) main'e birleştirildi.

**İki çalışma aynı sonuca vardı.**

## Kurulum farkları

| | Atay (`03_covid_lodo.py`) | Bengisu (`docs/13`) |
|---|---|---|
| Görev | Gün 0 → gün 2, 11 ve 28 (gün one-hot) | Gün 0 → gün 28 |
| Bölme | LODO, 6 fold | LODO, 6 fold (ayrıca hücre düzeyinde standart bölme) |
| Ön işleme | Her fold'da yalnız eğitim donörlerinden 2.000 HVG, CP10k + log1p (sızıntısız) | Hazırlanmış h5ad, CP10k + log1p (HVG hangi hücrelerden seçildi: açık soru) |
| Eşleşme | `donor` (aynı donör ve hücre tipi) ve `random` (orijinal) | Aynı donör; sonra aynı donör ve hücre tipi |
| Metrik | pertbench: pseudobulk pearson_δ, mse_top20, yön doğruluğu; 30 PC'de MMD/enerji | Düzleştirilmiş PCC, pseudobulk Δ-PCC, varyans oranı, permütasyon testi |
| Baseline | NoChange, PerturbationMean, Additive, ContextRidge | Copy-control (= NoChange), Mean-Day28 (= GlobalMean'in gün 28 karşılığı), Mean-Delta (= PerturbationMean) |

## Sonuçlar (Atay, 6 fold, 144 test koşulu)

| Model | RNA pearson_δ | RNA mse_top20 | Protein pearson_δ | Protein mse_top20 |
|---|---|---|---|---|
| NoChange | – | 0,201 | – | **0,183** |
| **PerturbationMean** | 0,283 | **0,170** | 0,066 | 0,192 |
| ContextRidge | **0,285** | 0,173 | 0,071 | **0,183** |
| MultiPert[donor] | 0,180 | 0,595 | 0,154 | 0,807 |
| MultiPert[random] | 0,182 | 0,597 | **0,155** | 0,805 |

**Gün bazında, sadece donör eşleşmeli versiyon.** Değerler pearson_δ, parantez içi mse_top20.

| Gün | RNA MultiPert | RNA PerturbationMean | Protein MultiPert | Protein PerturbationMean |
|---|---|---|---|---|
| 2 | 0,110 (0,567) | 0,289 (0,121) | 0,155 (0,785) | 0,047 (0,213) |
| 11 | 0,211 (0,595) | 0,379 (0,121) | 0,144 (0,830) | 0,063 (0,162) |
| 28 | **0,218** (0,623) | 0,181 (0,269) | **0,164** (0,806) | 0,089 (0,202) |

**Dağılım (RNA, 30 PC):**
- MultiPert'in MMD'si 1,85; değişim yok tahmininin 0,07.
- Tahmin edilen hücrelerin standart sapması ≈ 0; gerçek hücrelerinki 0,19.

**Eğitim:**
- Kayıp yaklaşık 4,5'te takılı kalıyor. THP-1 verisinde aynı kayıp 46'dan 2,8'e düşüyordu.
- Erken durma 22–51. epoch'ta.
- Fold başına 5–9 dk (CPU, 6 iş parçacığı).

## İki çalışmanın ortak bulguları
1. **Çöküş.**
   - Atay: tahmin std ≈ 0.
   - Bengisu: varyans oranı 10⁻¹⁰; 5.054 tahminde 3 farklı satır; tahminleri karıştırmak skoru değiştirmiyor.
   - Model girdiye bakmadan tek bir "aşı sonrası profil" üretiyor.
2. **Eşleşme fark yaratmıyor.** Donör içi ve rastgele eşleşme aynı sonucu veriyor (Atay: 0,180 / 0,182). Bengisu'da aynı hücre tipini zorunlu kılmak da değiştirmedi. Model girdiyi kullanmadığı için bu beklenen bir sonuç.
3. **Δ korelasyonu benzer, büyüklük çok yanlış.**
   - Gün 28 RNA Δ-PCC: Atay 0,218 (çıta 0,181), Bengisu 0,193–0,194 (Mean-Delta 0,190).
   - Protein Δ-PCC: Atay 0,154–0,164 (çıta 0,066–0,089), Bengisu 0,150 (Mean-Delta 0,103).
   - Ama hata (MSE) çıtanın 3–4 katı. Bengisu'da gün 28 MSE: RNA 0,077'ye karşı 0,007, ADT 0,664'e karşı 0,026.
   - Yorum: Model değişimin yönünü kabaca yakalıyor, ama donörün gün 0 durumunu korumuyor.
4. **Ham PCC yanıltıcı.** Bengisu'nun LODO PCC'si 0,615, ama Mean-Day28 baseline'ı da 0,616 alıyor. Bu yüzden delta metrikleri şart (CLAUDE.md kuralı).

## Neden olabilir? (hipotezler, test edilecek)
- **(a) Eğitim ayarı.** Öğrenme hızı veya adversarial kaybın ağırlığı. Kayıp düşmüyor, bu en olası aday. Test: lr 1e-4, adversarial ağırlık 0.
- **(b) Hedef yapısı.** Rastgele eşleşmiş hücre çiftlerinde MSE kaybı, matematiksel olarak koşul ortalamasını öğretir. Hücreler eşli olmadığı için bireysel hedef gürültü. Çözüm: MMD/OT gibi dağılım kaybı (hedef mimari, `PROJE_BAGLAMI.md` §9).
- **(c) Etki küçük.** Aşı etkisi nadir alt popülasyonda (`docs/sonuclar_tam_multimodal.md`). Ortalama değişim küçük; model "sabit profil" çözümüne düşüyor.

## Senkronizasyon önerisi
- **Ortak pipeline:** `03_covid_lodo.py`.
  - Sızıntısız ön işleme yapıyor, tüm günleri kapsıyor, pertbench tablosuna yazıyor.
  - Bengisu'nun 04 (çöküş) ve 05 (hücre tipi baseline'ları) scriptleri h5ad çıktısı bekliyor. 03'ün çıktısına (`fold_<donor>/multipert_predictions.csv`, pseudobulk) uyarlanabilir, ya da 03'e h5ad kaydı eklenir.
- **Sonraki deneyler** (paralel yürütülebilir):
  - (a) Düşük lr / adversarial kayıp kapalı (Atay, CPU).
  - (b) Δ'yı ölçekleyen kalibrasyon: MultiPert'in değişim yönü + PerturbationMean büyüklüğü. Basit ama kayda değer bir kontrol.
  - (c) Kayıp olarak MMD (Bengisu ile birlikte; GPU varsa Kaggle/okul PC).
- **Bengisu'ya sorular:**
  1. HVG / hazırlanmış h5ad hangi hücrelerden üretildi? Test donörü dahil mi?
  2. Kaç epoch, CPU mu GPU mu, hangi lr?
  3. Fold çıktıları (`output_lodo_celltype_<donor>_full/`) nerede?

## Dosyalar
- `results/multipert_covid_{donor,random}_celltypel1_s1/`:
  - `summary.csv`, `distribution_all.csv`, `timing_min.json`, `args.json`.
  - Model `.pth` dosyaları ve tahmin CSV'leri git dışında; scriptle yeniden üretilir.
- `results/multipert_covid_diagnostics_summary.csv`: Bengisu'nun özet tablosu.
