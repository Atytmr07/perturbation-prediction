# MultiPert Makale Notları

*Hazırlayan: Bengisu Atlı · Tarih: 06.10.2026 (el yazısı notlardan dijitalleştirildi, 07.10.2026)*
*Makale: Zhao vd., "MultiPert: An adversarial alignment and dual attention framework for single-cell multi-omics perturbation prediction", PLOS Comput Biol 2026. DOI 10.1371/journal.pcbi.1014054*

---

## 1. Özet ve Giriş (Abstract / Introduction)

- Mevcut birçok yöntem yalnızca **scRNA-seq**, yani tek modaliteli transkriptomik veri kullanıyor.
- **MultiPert'in farkı:** single-cell multi-omics kullanması. Orijinal çalışmada özellikle **RNA + protein** birlikte modelleniyor.
- MultiPert her modalite için **ayrı encoder** kullanıyor. RNA ve protein aynı şekilde işlenmiyor; her birinin biyolojik yapısına uygun ayrı temsil öğreniliyor.
- Bu encoder'lar önce ayrı ayrı **pretraining** aşamasından geçiyor.
- RNA ve protein temsillerini ortak bir latent alanda hizalamak için **adversarial training** kullanılıyor.
- Perturbation bilgisi modele basitçe bir etiket olarak verilmek yerine, hücresel temsille **dual-attention** mekanizması üzerinden birleştiriliyor.
- Çalışma, MultiPert'in hem **gen ekspresyonu** hem de **protein abundance** tahmini yaptığını gösteriyor.
- Makalede iki farklı biyolojik sistem kullanılıyor: **THP-1** ve **kidney** multi-omics veri setleri.
- **THP-1 bir insan donörü değil, bir hücre hattı.** Bu nedenle makalenin orijinal problemi, bizim hedeflediğimiz *unseen donor prediction* problemiyle aynı değil.
- MultiPert'in önemli iddialarından biri, eğitimde görmediği **unseen perturbation**'lara genelleyebilmesi.
- Ayrıca tahmin edilen RNA/protein profilleri üzerinden biyolojik mekanizmalar ve immün ilişkili yolaklar yorumlanabiliyor. Yani model sadece tahmin değil, bir miktar **interpretability** de hedefliyor.

**Giriş: motivasyon**
- Multi-omics veride temel ihtiyaç: RNA ve protein gibi farklı modaliteleri birlikte hizalayıp modellemek.
- Farklı modaliteler farklı biyolojik yapılar taşıdığı için **modaliteye özel encoder ve preprocessing** gerekiyor.
- Aynı perturbation RNA ve protein üzerinde farklı etkiler yaratabilir. Modelin bu katmanlara özgü yanıtları ayrı ayrı öğrenmesi gerekiyor.
- MultiPert bu problemi **modality-specific encoders + adversarial alignment + dual attention** ile çözmeye çalışıyor.
- Model THP-1 ve kidney verilerinde hem bilinen hem de görülmemiş perturbation'lar için test ediliyor.
- Ayrıca yalnızca tahmin değil; DEG örüntüleri, immune checkpoint ilişkileri ve pathway enrichment gibi biyolojik yorumlar da hedefleniyor.

## 2. Materyal ve Yöntem (Material and Methods)

### Neden iki modalite ayrı işleniyor?
- RNA ve protein için ayrı preprocessing ve ayrı encoder kullanılıyor.

### RNA preprocessing
- 10'dan az hücrede görülen genler çıkarılıyor.
- Her hücrenin toplam count'u 10.000'e normalize ediliyor.
- log1p dönüşümü uygulanıyor.
- En değişken 5000 gen seçiliyor.
- **Amaç:** gürültüyü azaltmak, boyutu düşürmek, modelin biyolojik olarak daha anlamlı genlere odaklanmasını sağlamak.

### Protein preprocessing
- Protein count'ları da hücre başına 10.000'e normalize ediliyor.
- Ardından yine log1p uygulanıyor.
- RNA'daki gibi 5000 özellik seçimi yok, çünkü protein sayısı çok az. Örneğin THP-1 verisinde sadece 4 protein var.

### RNA encoder: Zero-Inflated Negative Binomial VAE (ZINB-VAE)
- RNA için sıradan bir autoencoder yerine **ZINB-VAE** kullanılıyor.
- **Sebep:** scRNA-seq verisi çok fazla 0 içeriyor ve overdispersed. Klasik Gauss varsayımıyla iyi modellenemeyebilir.
- Encoder, RNA profilini **32 boyutlu** latent temsile indiriyor: 5000 gen → 32 latent feature.
- VAE iki şey öğreniyor: latent ortalama μ ve latent varyans σ². Sonra buradan latent z örnekleniyor.
- **Kayıp** iki parçadan oluşuyor: reconstruction loss ve KL divergence.
- **Amaç:** hem veriyi yeniden oluşturabilmek hem de düzgün bir latent uzay öğrenmek.

### Protein encoder: klasik autoencoder
- Protein için daha basit bir AE kullanılıyor.
- Protein profili d_ADT → 32 boyutlu latent temsile dönüştürülüyor.
- Decoder tekrar protein profilini oluşturuyor.
- **Kayıp:** MSE.
- Burada ZINB kullanılmıyor, çünkü protein verisinin yapısı RNA kadar sparse ve count dağılımı ağırlıklı değil.

### Bu iki encoder neden önce ayrı ayrı pretrain ediliyor?
- Model doğrudan büyük ortak eğitime başlatılmıyor.
- Önce RNA encoder RNA'nın yapısını, protein encoder proteinin yapısını öğreniyor.
- Pretraining yalnızca **10 epoch**.
- Daha sonra bu öğrenilmiş ağırlıklar, integrative training'in başlangıç ağırlıkları olarak kullanılıyor.
- Yani önce her modaliteyi kendi içinde öğren, sonra bunları birleştir.
- Bu özellik küçük veri setlerinde daha stabil bir başlangıç sağlayabilir.

### Perturbation embedding nasıl oluşturuluyor?
- Perturbation, "IRF1" veya "STAT2" gibi düz bir kategori olarak modele verilmiyor.
- **Gene Ontology** tabanlı bir bilgi grafiği kullanılıyor.
- Genler ile GO terimleri arasında bağlantılar kuruluyor.
- Genlerin birbirine ne kadar benzediği, ortak GO terimleri üzerinden **Jaccard similarity** ile hesaplanıyor.
- Her gen için en benzer 20 gen seçiliyor. Böylece bir gene–gene graph oluşturuluyor.
- Bu graftan **GNN tabanlı** embedding çıkarılıyor.
- MultiPert sıfırdan öğrenmek yerine **GEARS** tarafından önceden eğitilmiş perturbation embedding'lerini kullanıyor.
- **Amaç:** Model bir geni hiç görmemiş olsa bile, biyolojik olarak benzer genlerden bilgi transferi yapabilsin.
- Bu özellikle unseen perturbation prediction için kritik.

### Integrative training'de iki tür hücre temsili öğreniliyor
- Her modaliteden iki farklı embedding çıkarılıyor: **specific embedding** ve **shared embedding**.
  - **Specific embedding:** RNA'ya özgü veya proteine özgü bilgi.
  - **Shared embedding:** RNA ve protein için ortak olan hücresel bilgi.
- Yani model bilinçli olarak *shared biology* ile *modality-specific biology*'yi ayırmaya çalışıyor.

### Shared encoder ne yapıyor?
- RNA ve protein girdilerini ortak bir latent space'e taşıyor.
- Ama yalnızca aynı boyuta taşımak yetmez. RNA'nın shared embedding'i ile proteinin shared embedding'inin gerçekten benzer dağılımlara gelmesi isteniyor.
- Bunun için **adversarial training** kullanılıyor.

### Adversarial network neden var?
- Bir **discriminator** var. Shared embedding'e bakıp "Bu RNA'dan mı geldi, proteinden mi?" diye tahmin etmeye çalışıyor. Etiketler: RNA = 1, protein = 0.
- Discriminator doğru ayırmayı öğreniyor.
- **Generator** (shared encoder) ise discriminator'ı şaşırtmaya çalışıyor. Hedefi, discriminator çıktısını yaklaşık **0,5** yapmak.
- Yani discriminator "Bu embedding RNA mı protein mi, ayırt edemiyorum" duruma gelirse, shared latent representation gerçekten **modality-agnostic** olmuş kabul ediliyor.

### Shared RNA ve protein embedding'leri ayrıca füzyonlanıyor
- RNA shared embedding'i z_d^t ve protein shared embedding'i z_d^p birleştiriliyor (concatenate): [z_d^t ; z_d^p].
- Sonra bir MLP'den geçirilerek z_f, yani **fused embedding** oluşturuluyor.
- Bu temsil, RNA ve proteinden gelen ortak bilgiyi tek vektörde birleştiriyor.

### Perturbation embedding de modaliteye özel hale getiriliyor
- Aynı perturbation, RNA ve protein düzeyinde aynı etkiyi göstermek zorunda değil.
- Örneğin bir gen knockout'u RNA'da büyük değişikliğe, proteinde ise daha küçük veya gecikmeli değişikliğe yol açabilir.
- Bu yüzden perturbation embedding'i doğrudan kullanılmıyor. Ayrı encoder'lardan geçirilerek:
  - **transcriptome-adapted** perturbation embedding,
  - **proteome-adapted** perturbation embedding oluşturuluyor.

### Dual attention ne yapmaya çalışıyor?
- Hücrenin latent durumu ile perturbation bilgisini birleştiriyor. İki aşaması var:
  1. **Cross attention:** hücre embedding'i ile perturbation embedding'i arasındaki ilişkiyi öğreniyor.
  2. **Channel attention:** hangi latent feature'ın daha önemli olduğunu ağırlıklandırıyor. Yani amaç: "Bu hücrede bu perturbation uygulanınca hangi özellikler daha önemli hale geliyor?"
- Sonuçta perturbed cell temsili (perturbation uygulanmış hücre) oluşturuluyor.

### Decoder ne yapıyor?
- Attention sonrasında elde edilen perturbed representation decoder'lara gidiyor.
- RNA decoder ŷ^RNA, protein decoder ŷ^protein üretiyor.
- Bunlar tahmin edilen perturbation sonrası profiller.

### Kayıplar
- **Reconstruction loss:** Modelin temel tahmin kaybı. Hem RNA hem protein tahmin hatası aynı loss içinde toplanıyor. Model iki modaliteyi aynı anda doğru tahmin etmeye çalışıyor.
- **Discriminator loss:** Discriminator'ın amacı RNA ile protein shared embedding'lerini ayırmak.
- **Generator adversarial loss:** Generator discriminator'ı kandırmaya çalışıyor; shared embedding'lerin modalite kaynağının belirsizleşmesini istiyor.
- **Toplam generator loss:** reconstruction loss + generator adversarial loss.

### Eğitim iki fazlı
1. Önce **discriminator** güncelleniyor: generator dondurulur (freeze), discriminator öğrenir.
2. Sonra **generator** güncelleniyor: discriminator dondurulur, generator hem tahmin yapmayı hem de discriminator'ı şaşırtmayı öğrenir.
- Bu döngü her epoch boyunca tekrar ediliyor.

### Optimizer ve learning rate
- **Adam** kullanılıyor.
- Generator: lr = 0,001
- Discriminator: lr = 0,002. Discriminator biraz daha yüksek learning rate ile eğitiliyor.

## 3. Kullanılan veri setleri, metrikler ve karşılaştırılan yöntemler

### Veri setleri
- **THP-1 dataset**
  - ECCITE-seq ile oluşturulmuş.
  - 8.984 hücre içeriyor; 16.826 gen ve 4 protein var.
  - Başlangıçta 10 single-gene knockout var. 10'dan az hücre içeren perturbation çıkarıldığı için analizlerde 9 perturbation kullanılıyor.
- **Kidney dataset**
  - CaRPool-seq ile oluşturulmuş.
  - 8.802 hücre içeriyor; 20.839 gen ve 7 protein var.
  - 7 perturbation içeriyor.
- Ayrıca model **transcriptome–epigenome** ve **epigenome–proteome** gibi farklı multimodal veri setlerinde de denenmiş.

### Değerlendirme metrikleri
- **MSE:** Tahmin ile gerçek değer arasındaki hatayı ölçüyor. Düşük olması daha iyi.
- **PCC:** Tahmin edilen ve gerçek profiller arasındaki korelasyonu ölçüyor. 1'e yaklaştıkça daha iyi.
- **Önemli nokta:** Bu PCC hücreye özgü çeşitliliği tam olarak ölçemiyor. Bizim fark ettiğimiz gibi, model perturbation başına benzer profiller üretse bile PCC yüksek çıkabiliyor.

### MultiPert hangi yöntemlerle karşılaştırıldı?
- scGen, CPA, CoupleVAE, scPRAM, scGPT.
- Bu modellerin çoğu esas olarak scRNA-seq tabanlı. MultiPert'in avantajı RNA'nın yanında proteini de kullanması.

## 4. Sonuçlar

### THP-1 RNA sonuçları
- Tüm genlerde: medyan MSE ≈ 0,09, medyan PCC ≈ 0,78.
- Makaleye göre MultiPert diğer modellerden daha düşük MSE ve daha yüksek PCC elde ediyor.

### DEG analizi
- DEG = Differentially Expressed Gene. Perturbation sonrası en çok değişen genlere bakılıyor.
- Top 50 DEG değerlendiriliyor. MultiPert: medyan MSE = 0,37, medyan PCC = 0,88.
- **Amaç:** sadece genel ekspresyonu değil, perturbation'ın gerçekten etkilediği kritik genleri tahmin etmek.

### MARCH8 örneği
- MARCH8 knockout örnek perturbation olarak ayrıntılı inceleniyor.
- MultiPert'in tahminleri ile gerçek ekspresyonlar karşılaştırılıyor. Yaklaşık PCC ≈ 0,89.
- Top 20 DEG için genin arttı mı, azaldı mı olduğu da karşılaştırılıyor. Modelin yalnızca değeri değil, değişim yönünü de yakalaması bekleniyor.

### Protein sonuçları
- MultiPert: medyan MSE ≈ 0,07, medyan PCC ≈ 0,79.
- **Bizim reproduction:** protein PCC ≈ 0,788.
- Makale ayrıca protein sonuçlarının perturbation'lar arasında daha stabil olduğunu söylüyor.

### Protein değişim yönü analizi
- Protein için sadece mutlak abundance değil, perturbed − control değişimi de inceleniyor.
- **Amaç:** protein arttı mı, azaldı mı sorusunu doğru tahmin etmek.
- MultiPert bazı proteinlerde diğer yöntemlerden daha doğru yön tahmini yapıyor.

### Kidney dataset sonuçları
- MultiPert kidney veri seti üzerinde de test ediliyor. Amaç, modelin sadece THP-1'e özel olmadığını göstermek.
- Çoğu metrikte en iyi veya en iyiye yakın sonucu veriyor.
- Bazı protein sonuçlarında PCC yaklaşık 0,98 seviyesine çıkıyor.

### Specific ve shared embedding analizi
- Model iki tür temsil öğreniyor: omics-specific embedding ve omics-shared embedding.
- **Specific embedding:** RNA ve protein birbirinden ayrılıyor. Bu, modaliteye özgü biyolojik bilginin korunduğunu gösteriyor.
- **Shared embedding:** RNA ve protein temsilleri birbirine yaklaşıyor. Bu da ortak biyolojik temsilin öğrenildiğini gösteriyor.

### Adversarial alignment analizi
- RNA ve protein shared embedding'lerinin birbirine yaklaşıp yaklaşmadığı ölçülüyor.
- Kullanılan metrikler: **MMD** ve **Wasserstein distance**.
- Eğitim ilerledikçe bu mesafeler azalıyor.
- Yazarların yorumu: adversarial network, RNA ve protein latent uzaylarını hizalıyor.

### Perturbation embedding analizi
- Aynı perturbation için RNA ve protein embedding'leri birebir aynı değil.
- Örneğin MARCH8 için transcriptome-specific ve proteome-specific perturbation embedding'leri ayrı öğreniliyor.
- Bunun nedeni: aynı gen knockout'unun RNA ve protein düzeyinde farklı etkiler yaratabilmesi.

### Perturbation bilgisini hücre ile birleştirme yöntemleri
- Dört yöntem deneniyor: addition, multiplication, concatenation, cross-attention.
- En iyi sonuç: cross-attention (MultiPert-T). Addition ikinci sırada.
- Yazarların sonucu: perturbation etkisi basit toplama veya concatenation'dan daha karmaşık.

### Ablation deneyleri
- **MultiPert-WA:** adversarial network çıkarılıyor.
- **MultiPert-WS:** specific encoder yerine shared encoder kullanılıyor.
- **Sonuç:** RNA tarafında specific encoder önemli; protein tarafında adversarial alignment önemli. Full MultiPert iki varyanttan da daha iyi. Yani model parçalarının birlikte çalışması performansı artırıyor.

### Unseen perturbation prediction
- Burada **leave-one-out cross-validation** kullanılıyor.
- Örneğin ATF2 tamamen train'den çıkarılıyor, model diğer perturbation'larla eğitiliyor, sonra ATF2 response'u tahmin ediliyor.
- Bu işlem 9 perturbation için ayrı ayrı uygulanıyor. Bu gerçekten bir unseen perturbation generalization testi.

### GEARS ile karşılaştırma
- GEARS, unseen perturbation prediction için güçlü bir baseline.
- MultiPert daha düşük MSE ve daha yüksek PCC elde ediyor.
- Yazarların açıklaması: MultiPert RNA + protein kullanıyor, GEARS yalnızca transcriptomics kullanıyor. Ayrıca GEARS protein prediction yapamıyor.

### PDL1 üzerinden biyolojik yorum
- PDL1 bir immune checkpoint proteini. Model farklı knockout'ların PDL1 üzerindeki etkisini tahmin ediyor.
- Örneğin ATF2 knockout → PDL1 azalıyor. Buradan "ATF2, PDL1'in pozitif regülatörü olabilir" yorumu yapılıyor. Bu ilişki literatürde de destekleniyor.

### IRF7 örneği
- MultiPert, IRF7 knockout → PDL1 azalmasını tahmin ediyor.
- Bu sonuç, IRF7'nin bilinen transcriptional activator rolüyle uyumlu bulunuyor.

### MARCH8 ve PDL1
- 9 perturbation arasında PDL1 üzerindeki en güçlü değişimlerden biri MARCH8 knockout'ta görülüyor. Bu nedenle MARCH8 ayrıca detaylı inceleniyor.
- MultiPert'in DEG değişimlerini GEARS'tan daha doğru yakaladığı gösteriliyor.

### GO enrichment analizi
- Tahmin edilen DEG'lere Gene Ontology enrichment uygulanıyor.
- Özellikle şu süreçlerle ilişkili pathway'ler bulunuyor: immune response, inflammatory regulation, cellular defense.
- **Amaç:** modelin tahminlerinin biyolojik olarak anlamlı olup olmadığını kontrol etmek.

---

## Ek: Notların bizim kod analizi ve reproduction'ımızla karşılaştırması

*(Atay / Claude tarafından eklendi. Kaynak: `external/MultiPert/code`, `results/multipert_original/`, `docs/sonuclar_gece1.md`)*

| Notlardaki bilgi | Kodda / bizim sonuçlarda | Durum |
|---|---|---|
| RNA: <10 hücrede görülen gen çıkarılır, CP10k + log1p, 5000 HVG | `preprocess_transcriptomics`: aynısı | ✔ Uyumlu. Not: HVG seçimi test hücreleri dahil tüm veride yapılıyor (sızıntı) |
| Protein: CP10k + log1p, özellik seçimi yok | `preprocess_proteomics`: aynısı | ✔ (ADT için daha standart olan CLR değil) |
| Latent 32, pretraining 10 epoch | Log: "Epoch 10, … pretraining loss" | ✔ |
| THP-1: 8.984 hücre, 16.826 gen, 4 protein, 10 KO → 9 | Veride IFNGR2 sadece 4 hücre, filtreyle çıkıyor | ✔ |
| Adam, lr 0,001 / 0,002; önce discriminator, sonra generator | `trainer.py`: aynısı; early stopping patience 20 | ✔ |
| Toplam generator kaybı = reconstruction + adversarial | `total_generator_loss = reconstruction_loss + generator_adv_loss` (ağırlık 1:1) | ✔ |
| RNA medyan MSE 0,09 / PCC 0,78; DEG 0,37 / 0,88; protein 0,07 / 0,79 | Bizim CPU reproduction: 0,087 / 0,779; 0,372 / 0,882; 0,066 / 0,789 | ✔ Yeniden üretildi |
| "PCC hücreye özgü çeşitliliği ölçemiyor" | Tahminlerin hücreler arası std'si gerçeğinden ~30 kat küçük. Delta metrikleriyle MultiPert basit eğitim ortalamasını geçemiyor (protein `pearson_delta` 0,556'ya karşı 0,953) | ✔ Notlardaki şüpheyi doğruluyor |
| Kontrol hücresi → perturbe hücre eşleşmesi | Notlarda yok. Kodda eşleşme **rastgele** (`sample_data`), split her perturbation içinde hücre düzeyinde 60/20/20 | ➕ Notlara eklenmeli: bizim donör kurgusu için kritik |
| Kidney: 20.839 gen | Bizim önceki özetimizde 20.639 yazıyordu | ⚠ Makaleden kontrol edilmeli |

**Bizim proje açısından en önemli üç nokta (notlardan):**
1. THP-1 bir hücre hattı, donör yok. Makalenin genelleme iddiası **görülmemiş perturbation** üzerine; bizimki **görülmemiş donör**.
2. Modelin MSE ile eğitilmesi ve rastgele kontrol eşleşmesi, ortalamaya yakın, çeşitliliği olmayan tahminlere yol açıyor. Makaledeki PCC bunu gizliyor.
3. Modalite-özel / ortak embedding ayrımı ve modaliteye özel perturbation embedding fikri, bizim COVID uyarlamamızda (İz A) korunmaya değer. Adversarial hizalama ise eksik modaliteyi desteklemiyor; İz B/C'de PoE/MoE tarzı entegrasyonla değiştirilebilir.
