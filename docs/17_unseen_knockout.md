# MultiPert: görülmemiş knockout testi (THP-1)

*Scriptler: `scripts/multipert/08_gears_embeddings.py`, `scripts/multipert/09_unseen_knockout.py` · sonuçlar: `results/multipert_unseen_ko_*/per_knockout.csv`, `summary.csv` · loglar: `results/multipert_unseen_ko_{A,B,film}.log`*

## Neden?
Makalenin THP-1 bölmesi her knockout'un hücrelerini 60/20/20 bölüyor. Bu yüzden test knockout'u eğitimde de var ve orada `PerturbationMean` tavan (bkz. `docs/16`). Modelin gerçekten genelleyip genellemediğini görmek için cevabı eğitimde hiç olmayan bir test gerekiyor.

## Kurulum
- **Leave-one-knockout-out:** 9 knockout'un her biri sırayla dışarıda bırakılıyor.
  - MultiPert kalan 8 knockout'la eğitiliyor (80/20 eğitim/doğrulama).
  - Dışarıdaki knockout'un tüm hücreleri, o genin perturbation vektöründen tahmin ediliyor.
- Kontrol eşleşmesi, ön-eğitilmiş kodlayıcılar ve seed (1), `main.py` ile aynı.
- **İki farklı gen vektörü kullanıldı:**
  - **shipped:** MultiPert ile gelen `pert_embeddings.npz`. GEARS 10 knockout'un hepsiyle eğitilmiş, yani test geni vektöre sızmış olabilir.
  - **gears:** GEARS, test geni olmadan her fold için yeniden eğitildi (`08_gears_embeddings.py`). Notebook'tan sapmalar: 5 epoch (20 değil) ve MultiPert'in 5.000 HVG'si + knockout genleri; CPU süresi yüzünden.
- **Baseline'lar** (test knockout'unun cevabını hiç kullanmıyor):
  - `NoChange`: kontrol ortalaması.
  - `LeaveOutMean`: kontrol ortalaması + diğer 8 knockout'un ortalama etkisi.
- **Metrikler:** pertbench delta metrikleri (knockout başına hücre ortalaması üzerinden) + 30 PC uzayında MMD. 9 knockout'un ortalaması raporlanıyor.

## Sonuçlar (9 knockout ortalaması)

| Model | RNA delta PCC | RNA top-20 MSE | RNA MMD | Protein delta PCC | Protein top-20 MSE | Protein MMD | Yayılım RNA / protein |
|---|---|---|---|---|---|---|---|
| NoChange | – | 0,394 | 0,158 | – | 0,004 | 0,062 | – |
| **LeaveOutMean** | **0,688** | **0,243** | **0,099** | **0,460** | **0,004** | **0,053** | – |
| MultiPert original, shipped | 0,564 | 0,272 | 1,284 | 0,448 | 0,067 | 1,746 | 0 / 0 |
| MultiPert original, gears | 0,583 | 0,265 | 1,268 | 0,387 | 0,099 | 1,673 | 0 / 0 |
| MultiPert film_mmdmean, gears | 0,468 | 0,291 | 0,186 | 0,142 | 0,013 | 0,260 | 0,39 / 0,23 |

**Knockout bazında RNA delta PCC:**

| Knockout | LeaveOutMean | original, shipped | original, gears | film_mmdmean, gears |
|---|---|---|---|---|
| ATF2 | **0,89** | 0,56 | 0,54 | 0,65 |
| CAV1 | **0,85** | 0,20 | 0,60 | 0,55 |
| ETV7 | **0,66** | 0,59 | 0,63 | 0,44 |
| IFNGR1 | 0,12 | **0,25** | 0,02 | −0,02 |
| IRF1 | 0,56 | 0,54 | **0,62** | 0,52 |
| IRF7 | **0,66** | 0,65 | 0,56 | 0,41 |
| MARCH8 | 0,82 | 0,79 | **0,84** | 0,76 |
| PDL1 | **0,76** | 0,67 | 0,63 | 0,31 |
| STAT2 | **0,87** | 0,83 | 0,82 | 0,60 |

## Yorum
1. **MultiPert, görülmemiş knockout'ta "diğer knockout'ların ortalaması"nı geçemiyor.**
   - Hangi vektörle olursa olsun: RNA delta PCC 0,56–0,58'e karşı 0,69.
   - Proteinde top-20 hata 15–25 kat yüksek; "hiç değişmez"den bile kötü.
   - `NoChange`'i ise RNA'da geçiyor (0,27'ye karşı 0,39). Yani gen vektöründen bir miktar bilgi alıyor, ama bu bilgi basit ortalamadan daha değerli değil.
2. **Sızıntının etkisi küçük.**
   - Sızıntısız vektörle RNA ortalaması değişmiyor (0,56 → 0,58), protein biraz düşüyor (0,45 → 0,39).
   - Belirgin fark tek knockout'ta: IFNGR1. MultiPert'in baseline'ı geçtiği tek knockout buydu (0,25 > 0,12). Sızıntısız vektörle bu 0,02'ye düşüyor.
3. **Orijinal modelde tahminler hücreden bağımsız** (yayılım 0). Bu, `docs/15`'teki dikkat katmanı bulgusunu görülmemiş knockout testinde de doğruluyor.
4. **FiLM + MMD + ortalama kaybı hücre çeşitliliğini geri getiriyor, ama genellemeyi iyileştirmiyor.**
   - İyileşenler: Yayılım 0,39 ve 0,23. MMD orijinale göre çok daha düşük: RNA 0,19'a karşı 1,27, protein 0,26'ya karşı 1,67. Protein top-20 hata da düşüyor: 0,013'e karşı 0,099.
   - Kötüleşenler: Ortalama değişim zayıflıyor; RNA delta PCC 0,47, protein delta PCC 0,14.
   - Dağılımda bile `NoChange`'i geçemiyor.
   - Görülmemiş bir genin etkisini bilmek için gen vektörünün iyi olması gerekiyor. Hücreyi kullanmak tek başına bu sorunu çözmüyor.

## Sınırlılıklar
- **Tek seed.** Knockout bazındaki sayılar gürültülü (örneğin CAV1: 0,20 ve 0,60). Ortalamalar daha güvenilir.
- **GEARS ayarları farklı:** 5 epoch ve HVG'yle sınırlı gen seti, notebook'taki ayarlar değil. Shipped vektörlerle sonucun benzer çıkması, bu farkın sonucu değiştirmediğini gösteriyor.
- **GEARS'ın kendisiyle karşılaştırılmadı.** Makalenin "MultiPert > GEARS" iddiası test edilmedi.
- **Sadece 9 knockout ve tek hücre hattı var.**
