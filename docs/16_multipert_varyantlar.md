# MultiPert varyantları: hücreyi çıktıya taşımak (THP-1)

*Script: `scripts/multipert/07_variants.py` · sonuçlar: `results/multipert_variant_*/rescored_summary.csv`, `results/multipert_variants.log`*

## Kurulum
Bütün varyantlar aynı ayarlarla çalıştı:
- Makalenin THP-1 verisi.
- Aynı rastgele kontrol eşleşmesi ve aynı 60/20/20 bölme (seed 1).
- Aynı ön-eğitilmiş kodlayıcılar.

Varyantlar arasında sadece aşağıda yazan parça değişiyor. Puanlama `02_rescore.py` ile yapıldı: knockout başına test hücresi ortalamaları üzerinden, 9 knockout'un ortalaması.

| Varyant | Değişiklik |
|---|---|
| original | Yok |
| residual | z = hücre + attn ⊙ w |
| film | z = hücre · (1 + γ(p)) + β(p) |
| film_wide | film + protein çözücüsü 64 → 32 → 4 |
| film_mmd | film_wide + her knockout için tahmin ve gerçek hücre grupları arasında MMD kaybı (+ 0,1 × MSE) |

## Sonuçlar

**Yayılım:** Aynı knockout içinde tahmin edilen hücrelerin ortalama standart sapması. Gerçek hücrelerde RNA için 0,226, protein için 0,242.

| Varyant | Yayılım RNA | Yayılım protein | RNA delta PCC | RNA top-20 MSE | Protein delta PCC | RNA MMD | Protein MMD | Makale PCC (RNA) |
|---|---|---|---|---|---|---|---|---|
| original | **0,000** | **0,000** | 0,833 | 0,010 | 0,575 | 1,175 | 1,380 | 0,774 |
| residual | 0,030 | 0,009 | 0,791 | 0,026 | 0,579 | 0,476 | 1,357 | 0,764 |
| film | 0,033 | 0,018 | 0,790 | 0,021 | 0,567 | 0,457 | 1,311 | 0,762 |
| film_wide | 0,011 | 0,043 | 0,712 | 0,063 | 0,580 | 1,059 | 1,130 | 0,770 |
| film_mmd | **0,273** | **0,201** | 0,647 | 0,029 | −0,056 | **0,059** | **0,140** | 0,606 |
| NoChange | – | – | – | 0,418 | – | 0,176 | 0,079 | – |
| PerturbationMean (eğitim hücreleri) | – | – | **0,861** | **0,007** | **0,953** | ~0 | ~0 | – |

## Yorum
1. **Sadece mimariyi düzeltmek yetmiyor.**
   - Residual ve FiLM ile hücre bilgisi çıktıya teknik olarak ulaşıyor.
   - Ama MSE ve rastgele eşleşme yüzünden model hücreyi neredeyse yok saymayı öğreniyor: yayılım gerçeğin 0,23'üne karşı sadece 0,03.
   - Ortalama metrikler biraz kötüleşiyor; dağılım uzaklığı (MMD) iyileşiyor ama "hiç değişmez"den hâlâ kötü.
2. **Grup karşılaştıran kayıp (MMD) gerçekçi hücre çeşitliliği üretiyor.**
   - Yayılım 0,27 ve 0,20; gerçek 0,23 ve 0,24.
   - Dağılım uzaklığı en iyi değerinde: RNA MMD 0,06. Orijinal 1,18; NoChange 0,18.
   - Bedeli: Ortalama değişim kötüleşiyor. RNA delta PCC 0,65; proteinde delta PCC ~0, yani protein ortalama değişimi kayboluyor.
   - Ham PCC de düşüyor (0,77 → 0,61), çünkü tahmine hücreden hücreye çeşitlilik ekleniyor.
3. **Protein çözücüsünü genişletmek protein delta'sını iyileştirmedi** (0,58). Darboğaz, protein tarafındaki zayıflığın ana sebebi değil gibi görünüyor. CLR normalizasyonu henüz denenmedi.
4. **Bu kurguda hiçbir varyant `PerturbationMean`'i geçmiyor.**
   - Test knockout'larının hücreleri eğitimde de olduğu için, eğitimdeki hücrelerin kendisi hem ortalamada hem dağılımda tavan (MMD ~0).
   - THP-1 interpolasyon bölmesi, hücreyi kullanmanın faydasını göstermeye uygun değil.
   - Fayda ancak cevabın eğitimde olmadığı testlerde görülebilir: görülmemiş knockout ya da görülmemiş donör/hücre tipi.

## Sınırlılıklar
- Her varyant tek seed ile çalıştı. film_wide 37. epoch'ta erken durdu; kararsız olabilir.
- MMD ağırlığı ve bant genişliği ayarlanmadı.
- Protein CLR normalizasyonu ve görülmemiş knockout testi henüz yapılmadı.

## Ek: ortalama + MMD kaybı ve CLR
Log: `results/multipert_variants2.log`.

**Yeni varyantlar:**
- **film_mmdmean:** Rastgele çiftlerdeki MSE yerine, her knockout grubu için MMD + grup ortalaması kare hatası.
- **film_mmdmean_clr:** Aynısı, ama protein CLR ile normalize edildi (her protein hücreler boyunca). Kodlayıcılar yeniden ön-eğitildi.

| Varyant | Yayılım RNA / protein | RNA delta PCC | RNA MMD | Protein delta PCC | Protein yön doğruluğu | Protein MMD |
|---|---|---|---|---|---|---|
| original | 0 / 0 | 0,833 | 1,175 | 0,575 | 0,64 | 1,380 |
| film_mmd | 0,27 / 0,20 | 0,647 | 0,059 | −0,056 | 0,58 | 0,140 |
| film_mmdmean | 0,31 / 0,21 | 0,622 | 0,069 | 0,486 | 0,61 | 0,107 |
| film_mmdmean_clr* | 0,30 / 0,23 | 0,667 | 0,062 | **0,586** | **0,83** | **0,032** |
| PerturbationMean (CP10k / CLR*) | – | 0,861 | ~0 | 0,953 / 0,964* | 0,86 / 0,97* | ~0 |
| NoChange (CP10k / CLR*) | – | – | 0,176 | – | – | 0,079 / 0,154* |

*\*CLR varyantının protein sayıları CLR uzayında. Kendi baseline'larıyla karşılaştırılmalı, diğer varyantların protein sayılarıyla doğrudan değil.*

**Yorum:**
- **Ortalama kaybı, MMD'nin kaybettiği protein ortalamasını geri getiriyor:** protein delta PCC −0,06 → 0,49.
- **CLR ile protein en iyi değerine ulaşıyor:**
  - Delta PCC 0,59.
  - Yön doğruluğu 0,83.
  - Dağılım uzaklığı (MMD 0,032), ilk kez "hiç değişmez" baseline'ından (0,154) daha iyi.
- **Makalenin ham PCC'si CLR'de proteinde 0,02'ye düşüyor**, oysa değişim metrikleri iyileşiyor. CLR her proteini kendi içinde merkezlediği için, proteinler arası seviye farkı ham korelasyonu artık şişiremiyor. Bu da ham PCC'nin bu seviye farklarından beslendiğini doğrudan gösteriyor.
- **RNA ortalama değişimi orijinalin gerisinde kalıyor** (0,67'ye karşı 0,83).
- **Hiçbir varyant `PerturbationMean`'i geçmiyor.** Bu bölmede o zaten tavan.
