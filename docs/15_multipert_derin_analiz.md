# MultiPert Derin Analizi ve Donör-Farkında Genişletme (20 Ekim 2026)

Kaynaklar:
- Zhao vd., *PLOS Comput Biol* 22(3): e1014054 (2026). Makale metni okundu; denklemler sayfada görsel olduğu için metinden alınamadı.
- Kod: `external/MultiPert/code/`, ~900 satır, satır satır okundu.
- Bengisu'nun notları: `research/bengisu/multipert_makale_notlari.md`.
- Doğrulama scripti: `scripts/multipert/06_attention_check.py`.

## 1. Ne giriyor, ne çıkıyor?

**Görev:** Kontrol hücresinin RNA + proteini ve bir perturbation → aynı hücrenin perturbation sonrası RNA + proteini.

| | İçerik | Boyut (THP-1) |
|---|---|---|
| Girdi 1 | Kontrol hücresinin RNA'sı: CP10k + log1p, 5.000 HVG | 5.000 |
| Girdi 2 | Kontrol hücresinin proteini: CP10k + log1p | 4 (CD86, PD-L1, PD-L2, CD366) |
| Girdi 3 | Perturbation vektörü: GEARS'ın GO tabanlı gen embedding'i; bulunamazsa one-hot, 64'e tamamlanır | 64 |
| Hedef | Rastgele seçilmiş bir perturbe hücrenin RNA ve proteini (`sample_data`) | 5.000 + 4 |
| Çıktı | Tahmini perturbe RNA ve protein | 5.000 + 4 |

**Veriler:**
- **THP-1** (Papalexi 2021, ECCITE-seq): 8.984 hücre, 16.826 gen, 4 protein, 10 nakavt. 10 hücreden az olan çıkarılınca 9 nakavt kalıyor.
- **Böbrek** (CaRPool-seq, HEK-293): 8.802 hücre, 7 protein, 7 perturbation.
- **PBMC multiome** (Mimitou; RNA–ATAC ve ATAC–protein; IL2 + anti-CD3/CD28): Sonuçlar sadece ek tablolarda. ATAC'ın modele nasıl verildiği yazılmıyor; kodda ATAC desteği yok.

## 2. Mimari (koddaki gerçek akış)
1. **Ön-eğitim (10 epoch):**
   - RNA → ZINB-VAE, latent 32.
   - Protein → autoencoder, latent 32.
2. **Ortak kodlayıcılar:** RNA ve protein ayrı ayrı 32 boyuta iniyor. Füzyon MLP'si ikisini 32 boyutlu ortak temsile birleştiriyor.
3. **Hücre temsili:** `[özel (32) ‖ ortak (32)]` = 64 boyut, her modalite için ayrı.
4. **Perturbation kodlayıcı:** 64 → 64, her modalite için ayrı.
5. **DualFusionAttention:**
   - Cross-attention: sorgu = hücre, anahtar/değer = perturbation, 4 başlık.
   - Ardından channel attention: sigmoid ile kapı.
6. **Decoder:** RNA ve protein ayrı ayrı, 64 → modalite boyutu.
7. **Adversarial ayırıcı:** Ortak temsil RNA'dan mı proteinden mi geliyor, onu ayırt etmeye çalışıyor. Üretici 0,5 hedefiyle onu kandırmaya çalışıyor.
8. **Kayıp ve ayarlar:**
   - Kayıp: MSE(RNA) + MSE(protein) + adversarial BCE.
   - Adam: üretici 1e-3, ayırıcı 2e-3. Batch 512.
   - Erken durma patience 20; doğrulama kaybı ayırıcı terimlerini de içeriyor.

## 3. Kritik bulgu: tahmin hücreye hiç bağlı değil

`models.py` dosyasında, `DualFusionAttention.forward`:
```python
attn_output, _ = self.cross_attn(cell_embed.unsqueeze(0), perturb_embed.unsqueeze(0), perturb_embed.unsqueeze(0))
...
fused_embed = attn_output * channel_weights
```
- **Dizi uzunluğu 1.** `nn.MultiheadAttention` varsayılanda `(L, N, E)` bekliyor. `unsqueeze(0)` ile L = 1 oluyor: her hücrenin bakacağı **tek bir anahtar** var.
- **Softmax tek elemanda hep 1.** Çıktı = `out_proj(W_v · perturbation)`. Sorgunun (hücrenin) ağırlığa hiçbir etkisi yok.
- **Residual bağlantı yok.** Channel attention da bu çıktının fonksiyonu. Kodda residual'lı bir `MultiHeadAttentionLayer` sınıfı var, ama kullanılmıyor.
- **Sonuç:** Decoder'ın girdisi, yani tahmin, **sadece perturbation'ın fonksiyonu.** ZINB-VAE, ortak kodlayıcı ve adversarial hizalama tahmine hiç ulaşmıyor.

**Doğrulama** (`06_attention_check.py`):
- Farklı hücreler + aynı perturbation → çıktı farkı **0,0**.
- Farklı perturbation'lar → fark 0,9.
- Bizim THP-1 çalıştırmamızda: 1.402 tahmin, 9 perturbation, perturbation içi std **2·10⁻⁵**.
- COVID'de: Atay'da tahmin std 0; Bengisu'da 5.054 tahminde 3 farklı satır, karıştırma testi etkisiz.

**Anlamı:**
- MultiPert pratikte "her perturbation için öğrenilmiş bir ortalama profil" modeli. Bu, `PerturbationMean`'den bile zayıf: tahmine kontrol hücresinin durumunu da eklemiyor.
- Makaledeki THP-1 PCC 0,78, bu sabit profilin tek tek hücrelerle korelasyonu.
- Makaledeki UMAP'ler ve MMD/Wasserstein hizalama eğrileri ara katmanlara ait. Tahmine katkıları yok.
- **Makaledeki tanım da aynı** (PDF s. 7, `docs/papers/Zhao2026_MultiPert_PLOSCompBiol.pdf`):
  - Denklem 12: attn = MultiHeadAttn(Query = [z_c ‖ z_f], Key = Value = p_c).
  - Denklem 13: w = σ(W₄ · ReLU(W₃ · avgpool(attn))).
  - Denklem 14: z = attn ⊙ w.
  - Residual bağlantı yok; decoder'a z gidiyor. Her hücre için tek bir perturbation token'ı (anahtar) olduğundan, attn = W_o·W_v·p.
  - Yani bu bir kod hatası değil, **makaledeki tasarımın kendisi**: tahmin, tanım gereği hücreden bağımsız.

## 4. Değerlendirme (makalede)
- **Metrikler:** MSE ve PCC. Hücre × gen düzleştirilerek, ham değerlerde; delta (değişim) yok.
- **DEG metriği:** Tahmin ve gerçek için ayrı ayrı Wilcoxon ile top-50 gen seçiliyor. Ama metrik gerçek DEG'lerde hesaplanıyor.
- **Bölme:** Her perturbation'ın hücreleri 3:1:1. Testteki perturbation'lar eğitimde de var (interpolasyon).
- **Baseline'lar:** scGen, CPA, scPRAM, scGPT, CoupleVAE ve görülmemiş perturbation için GEARS.
  - Bu yöntemler RNA ve protein için ayrı ayrı çalıştırılmış.
  - "Perturbation ortalaması" ya da "değişim yok" gibi basit baseline yok.
- **Sonuçlar (THP-1):**
  - Tüm genler: medyan PCC 0,78, MSE 0,09.
  - Top-50 DEG: PCC 0,88, MSE 0,37.
  - Protein: PCC 0,79, MSE 0,07.
  - Böbrek, protein: PCC 0,98.
- **Ablasyon:**
  - Birleştirme yöntemleri karşılaştırılmış: toplama, çarpma, birleştirme, cross-attention. Tam model en iyi.
  - Modül çıkarma: adversarial yok (WA), özel kodlayıcı yok (WS).
- **Makalede donör, hasta veya batch hiç geçmiyor.** Sınırlılıklar bölümü yok.

## 5. Gene Ontology nasıl kullanılıyor? Verisi olmayan gen nasıl tahmin ediliyor?
- **Graf** (GEARS, Roohani vd., Nat Biotechnol 2024):
  - Her gen GO terimlerine bağlı.
  - İki genin benzerliği = ortak GO terimlerinin Jaccard indeksi.
  - Her gen en benzer K = 20 genle bağlanıyor.
- **Embedding:**
  - Her gene öğrenilebilir bir vektör veriliyor.
  - GNN bu vektörü graf komşularından gelen bilgiyle güncelliyor.
  - GEARS, Papalexi RNA verisinde 20 epoch eğitiliyor (`get_perturb.ipynb`). 4.005 gen için 64 boyutlu vektör çıkarılıp `pert_embeddings.npz`'ye kaydediliyor.
- **Görülmemiş gen:**
  - Bu gen hiç perturbe edilmemiş olsa da GO grafında komşuları var. Vektörü, işlevi benzer genlerin vektörlerine yakın oluyor.
  - Model bu vektörü decoder'dan geçiriyor, yani "GO'da komşu genler şöyle etki ediyordu" diye tahmin yapıyor.
  - §3'e göre tahmin sadece bu vektörün fonksiyonu. Görülmemiş gen tahmini = "GO vektörü → ortalama profil" eşlemesi.
- **Makaledeki test:**
  - 9 nakavtla leave-one-out yapılmış; sadece GEARS'tan iyi olduğu söyleniyor.
  - Sayılar sadece şekilde (Fig 5A–C).
- **Dikkat:**
  - (a) Notebook'ta GEARS'ın eğitim listesinde 10 nakavtın hepsi var. Leave-one-out'ta her fold için yeniden eğitildiği yazmıyor; eğitilmediyse dışarıda bırakılan genin vektörü onun verisini görmüş olur.
  - (b) 9 nakavtın hepsi aynı yolda (IFN-γ → JAK/STAT → PD-L1). "Diğer nakavtların ortalaması" baseline'ı test edilmemiş.
  - (c) LOO kodu repoda yok.
- **COVID'de:** Perturbation bir gen değil, aşıdan sonraki gün. GO vektörü kullanılamıyor; one-hot kullanılıyor. Görülmemiş "gün" tahmin edilemez, ama bizim sorumuz da bu değil.

## 6. Donör bilgisi nasıl kullanılabilir?
Hedef: donör 3 tahmin edilirken modelin **donör 3'ün kendi gün 0 hücrelerine** bakması ve diğer donörlerden **donör 3'e benzeyenlerin** cevabını ödünç alması.

| Yol | Fikir | Ne zaman işe yarar |
|---|---|---|
| **D0. Hücreyi geri bağla** | Residual: `z_sonra = z_hücre + Δ(z_hücre, p)`. Ya da FiLM: perturbation hücre temsilini ölçekleyip kaydırıyor | Şart. Bu olmadan donör bilgisi de tahmine ulaşamaz (§3) |
| **D1. Donör temsili (set encoder)** | Donörün gün 0 hücrelerinden bir vektör: `d = pool(enc(hücreler))`. Önce ortalama (CellFlow'daki gibi), sonra attention pooling. Hücre tipi oranları da eklenir. Gün 0 test donöründe de var, sızıntı yok | Görülmemiş donöre doğal genelleme (endüktif) |
| **D2. Donörler arası dikkat (retrieval)** | Sorgu = test donörünün `d`'si. Anahtarlar = eğitim donörlerinin `d`'leri. Değerler = o donörlerin gözlenen cevapları (gün × hücre tipi). Tahmin = benzer donörlerin ağırlıklı cevabı + model düzeltmesi | Ağırlıklar eşitse **`PerturbationMean`'e indirgeniyor**: çıta modelin özel bir hâli. Yorumlanabilir: "donör 3, en çok donör 5'e benziyor" |
| **D3. Epizodik LODO eğitimi** | Her adımda eğitim donörlerinden birini "sahte test" yap; model görülmemiş donöre genellemeyi öğrensin (meta-öğrenme) | Donör sayısı azken aşırı uyumu azaltır |
| **D4. Dağılım kaybı** | Rastgele çift MSE'si yerine, aynı donör × gün × hücre tipi grubunda tahmin ve gerçek hücre kümeleri arasında MMD / Sinkhorn. Ek olarak pseudobulk delta MSE | Hücreler eşli değil; dağılım kaybı ortalamaya çöküşü önler |
| **D5. Eksik modalite** | Hücre kodlayıcı yerine MultiVI / MIDAS ortak latent'i. RNA, ATAC ve protein; batch = assay | ATAC'ı dahil etmenin tek yolu |

**Model akışı (çalışma adı "DonorPert"):**
```
gün 0 hücreleri (donör k) ─► hücre kodlayıcı (MultiPert özel+ortak / MultiVI) ─► z_hücre
                         └─► set encoder ─► d_k ──┐
eğitim donörleri d_j, cevap Δ_j ──► donörler arası dikkat(d_k) ─► Δ_önsel
perturbation p (gün / gen GO / ilaç) ────────────┤
z_sonra = z_hücre + Δ_önsel + f(z_hücre, d_k, p)   (residual + FiLM)
   └─► decoder'lar ─► RNA, protein (, ATAC)
kayıp: MMD/Sinkhorn (hücre kümesi) + pseudobulk delta MSE; epizodik LODO
```

**Gerçekçi beklenti:** 6 donörle D2'nin benzerlik ağırlıkları gürültülü olur. Basit `ContextKNN` bile `PerturbationMean`'den kötüydü. Asıl test için daha çok donör lazım:
- Nöroblastom: 22 hasta.
- Parse 10M PBMC: 12 donör × 90 sitokin, sadece RNA. CellFlow'un verisi; donör modülü için test yatağı olabilir.

## 7. 2209 için önerilen fikir (tek paragraf)
Yayımlanan tek multimodal perturbation modeli MultiPert, tahmini hücreden ve donörden bağımsız tek bir profile indiriyor. Bunu kodda ve iki veride gösterdik. Önerimiz, MultiPert'in modaliteye özel ve ortak temsil fikrini koruyan, **donör-farkında** bir modeldir:
- (i) Hücre durumu residual/FiLM ile korunur.
- (ii) Donör, kendi tedavi öncesi hücrelerinden öğrenilen bir set temsiliyle tanımlanır.
- (iii) Donörler arası dikkat, benzer donörlerin cevabını ödünç alır. Çıta (`PerturbationMean`) bu modelin özel bir hâlidir.
- (iv) Eşli olmayan hücreler için dağılım kaybı (MMD/OT) kullanılır.
- (v) Eksik modaliteler için entegrasyon omurgası (MultiVI/MIDAS) eklenir.

**Değerlendirme:** Sızıntısız leave-one-donor-out, değişim metrikleri, çıtaya karşı. Veriler: COVID aşı (6 donör, RNA + protein + ATAC) ve nöroblastom (22 hasta).

**İlk 2 haftada yapılabilir ön deneyler:**
1. MultiPert'e residual eklenmiş hâli: çöküş kalkıyor mu?
2. D1 + D4 ile COVID LODO.
3. D2'nin pseudobulk versiyonu.

## 8. Açık sorular
- ~~Makaledeki denklem 12–14 residual içeriyor mu?~~ Cevaplandı (22 Ekim): İçermiyor; kod makaleyle tutarlı (§3).
- LOO deneyinde GEARS embedding'i fold başına yeniden eğitildi mi?
- PBMC multiome deneyinde ATAC nasıl verildi? Ek tablolar okunmalı.
