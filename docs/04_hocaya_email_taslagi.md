# Hilal Hoca'ya yanıt taslağı

**Konu:** Perturbation prediction: ilk literatür taraması ve benchmark iskeleti

---

Merhaba Hilal Hocam,

Gönderdiğiniz konu üzerinde çalışmaya başladık. Kısaca şunları yaptık:

**1. Literatür:** MultiPert (RNA+protein, PLOS CB 2026) ve MultiFlow (RNA+ATAC, bioRxiv 2026) makalelerini inceledik. Bunlara ek olarak alandaki başlıca yöntemleri ve benchmark çalışmalarını taradık. Multimodal tarafta dediğiniz gibi ciddi bir boşluk var. Mevcut iki yöntem az sayıda veri seti, protein ve perturbation üzerinde değerlendirilmiş ve basit lineer/additive baseline'larla karşılaştırılmamış. Ahlmann-Eltze vd. (Nat Methods 2025) RNA tarafında bu baseline'ların derin modelleri çoğu zaman geçtiğini gösteriyor.

**2. Donör bilgisi:** Bir nokta dikkatimizi çekti. CellFlow (Theis grubu, 2025), donörü kontrol hücrelerinin ortalamasıyla temsil ederek 12 donörlü Parse PBMC verisinde görülmemiş donörler için tahmin yapıyor. Ancak yalnızca RNA ile çalışıyor. Donör bilgisini **multimodal** veriyle birleştiren bir yöntem bulamadık. Bu ikisinin kesişimi iyi bir araştırma sorusu olabilir.

**3. Benchmark iskeleti:** Python'da küçük bir benchmark paketi yazdık. İçinde:
- görülmemiş perturbation, hücre tipi ve donör split'leri,
- delta tabanlı metrikler,
- donör-farkında bazıları dahil 8 baseline model,
- harici modeller (GEARS, CPA, MultiPert, MultiFlow vb.) için bir adaptör

var. Pipeline, sentetik veride ve iki gerçek multimodal veri setinde (Papalexi 2021 ECCITE-seq, Frangieh 2021 Perturb-CITE-seq) çalışıyor. İlk gözlemimiz şu: gerçek verilerde görülmemiş perturbation için baseline'lar arasında fark çok küçük. Papalexi'de gerçek donör olmadığı (yalnızca replikat olduğu) için donör-farkında modeller de fark yaratmıyor. Bu yüzden hem donörlü hem multimodal bir veri gerekiyor. En uygun aday OP3/NeurIPS 2023 verisi gibi görünüyor (PBMC, 3 donör, multiome).

Önerdiğimiz sıra şöyle:
- (i) MultiPert ve MultiFlow'u yeniden üretip aynı split'lerde baseline'larla karşılaştırmak,
- (ii) OP3 ve Parse verileriyle donör etkisini ölçmek,
- (iii) sonrasında donör-farkında multimodal bir model denemek.

Ayrıca mailinizdeki problem tanımı görselini tekrar inceleyip planı ona göre güncelleyeceğiz.

Uygun olduğunuz bir zamanda kısa bir görüşme yapabilirsek seviniriz. Derin modeller için GPU erişimi konusunda da (bölüm kümesi vb.) yönlendirmenize ihtiyacımız olacak.

İyi günler dileriz hocam.

Hasan Berk Berber, Emre Atay Tümer
