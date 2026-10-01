// Builds docs/Yapilacaklar_Sprint1.docx: the sprint task list with real (clickable) checkboxes.
// Run: node scripts/build_todo_docx.js   (needs `npm install docx`)
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, CheckBox,
  Footer, PageNumber, BorderStyle, ShadingType,
} = require("docx");

const FONT = "Calibri";
const ACCENT = "1F4E79";
const MUTED = "6B7280";

const box = () => new CheckBox({
  checked: false,
  checkedState: { value: "2611", font: "MS Gothic" },
  uncheckedState: { value: "2610", font: "MS Gothic" },
});

// level 0: main task (bold title + optional detail), level 1: sub-step
function task(title, detail, level = 0) {
  const runs = [box(), new TextRun({ text: "  " + title, bold: level === 0, font: FONT, size: level === 0 ? 22 : 20 })];
  if (detail) runs.push(new TextRun({ text: level === 0 ? "  " + detail : " " + detail, font: FONT, size: 20, color: level === 0 ? MUTED : "374151" }));
  return new Paragraph({
    children: runs,
    indent: { left: level === 0 ? 0 : 520, hanging: 0 },
    spacing: { before: level === 0 ? 140 : 30, after: level === 0 ? 30 : 30 },
    keepNext: level === 0,
  });
}

function note(label, text) {
  return new Paragraph({
    indent: { left: 520 },
    spacing: { before: 40, after: 60 },
    children: [
      new TextRun({ text: label + ": ", bold: true, font: FONT, size: 19, color: ACCENT }),
      new TextRun({ text, font: FONT, size: 19, color: "374151" }),
    ],
  });
}

function section(num, title, goal) {
  return [
    new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 60 }, keepNext: true,
      children: [new TextRun({ text: `${num}. ${title}`, font: FONT })] }),
    new Paragraph({ spacing: { after: 40 }, keepNext: true,
      children: [new TextRun({ text: goal, italics: true, font: FONT, size: 20, color: MUTED })] }),
    new Paragraph({ spacing: { after: 80 }, keepNext: true,
      children: [new TextRun({ text: "Sorumlu: ______________________     Hedef tarih: ____________", font: FONT, size: 18, color: MUTED })] }),
  ];
}

function para(text, opts = {}) {
  return new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text, font: FONT, size: 21, ...opts })] });
}

const S = [];

// ---------- header ----------
S.push(
  new Paragraph({ children: [new TextRun({ text: "CS4001 · BİTİRME PROJESİ", font: FONT, size: 16, bold: true, color: ACCENT, characterSpacing: 40 })] }),
  new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "Yapılacaklar: 2 Haftalık Sprint", font: FONT, size: 40, bold: true })] }),
  para("Donör-farkında, multimodal tek hücre perturbation tahmini. Hilal Hoca görüşmesine kadar yapılacak işlerin genel listesi. Her görev, altındaki adımlar ve \"bitti sayılır\" kriteriyle birlikte yazıldı; sorumlu ve tarih alanlarını birlikte dolduralım.", { color: "374151" }),
  new Paragraph({
    spacing: { before: 60, after: 60 },
    shading: { type: ShadingType.CLEAR, fill: "EAF1F8", color: "auto" },
    border: { left: { style: BorderStyle.SINGLE, size: 18, color: ACCENT, space: 6 } },
    children: [
      new TextRun({ text: "Sprint sonunda hocaya götürülecekler: ", bold: true, font: FONT, size: 20, color: ACCENT }),
      new TextRun({ text: "(1) MultiPert analizi ve zayıf noktaları, (2) COVID verisinde LODO baseline tablosu, (3) en az bir entegrasyon yönteminin COVID sonucu, (4) geliştirilmiş MultiPert tasarımı ve ilk prototip sonucu.", font: FONT, size: 20 }),
    ],
  }),
  new Paragraph({
    spacing: { after: 120 },
    children: [
      new TextRun({ text: "Google Docs notu: ", bold: true, font: FONT, size: 18, color: MUTED }),
      new TextRun({ text: "Kutular Word'de tıklanabilir. Google Docs'ta tıklanabilir olmazsa listeyi seçip Biçim → Madde işaretleri ve numaralandırma → Yapılacaklar listesi (checklist) ile çevirebilirsiniz.", font: FONT, size: 18, color: MUTED }),
    ],
  }),
);

// ---------- 0 ----------
S.push(...section(0, "Ortak düzen", "Herkes aynı yerden çalışsın, bilgi WhatsApp'ta kaybolmasın."));
S.push(
  task("Repoya herkes erişebiliyor", "github.com/Atytmr07/perturbation-prediction (public)"),
  task("Repoyu klonla ya da web'den gezinebildiğini kontrol et", null, 1),
  task("docs/ altındaki 07, 08 ve 10 numaralı dokümanları oku", "(veri setleri, iki iz planı, sprint)", 1),
  task("Araştırma teslim düzeni oturdu", null),
  task("research/SABLON.md şablonunu oku", "(özet, kaynaklı bulgular, uygulama bilgisi, kod merkezine iş, açık sorular)", 1),
  task("Her araştırma çıktısı research/<isim>/<konu>.md olarak repoya giriyor", null, 1),
  task("AI kuralları kabul edildi", "her iddiaya birincil kaynak linki; sayı ve fonksiyon adları kaynaktan kontrol; emin olunmayan her şey \"Açık sorular\"a", 1),
  task("Google Drive'da ortak klasör açıldı", "bu doküman + PDF'ler burada; kararlar ayrıca docs/ altına yazılır"),
);

// ---------- 1 ----------
S.push(...section(1, "MultiPert'i anlamak", "Hocanın ilk isteği: modelin nasıl çalıştığını ve nerede zayıf olduğunu satır düzeyinde bilmek."));
S.push(
  task("Makale okundu", "Zhao vd., PLOS Comput Biol 2026"),
  task("Şekil 1 ve Methods: mimari", "ZINB-VAE (RNA), AE (protein), shared encoder, fusion, dual attention, decoder, discriminator", 1),
  task("Methods: adversarial hizalama", "discriminator neyi ayırt ediyor, generator nasıl kandırıyor", 1),
  task("Methods: veri bölme", "hücre düzeyinde rastgele 3:1:1; neden interpolasyon görevi?", 1),
  task("Results: ablation ve görülmemiş perturbation (GEARS'a karşı LOO) deneyleri", null, 1),
  task("Kod okundu", "external/MultiPert/code (~900 satır)"),
  task("data_loader.py", "kontrol–perturbe eşleşmesi rastgele (sample_data); split per-perturbation 60/20/20; HVG tüm veride seçiliyor", 1),
  task("models.py", "her sınıfın girdi/çıktı boyutları; toplam parametre sayısı", 1),
  task("trainer.py", "generator/discriminator güncelleme sırası; lr 0.001 / 0.002; early stopping (patience 20)", 1),
  task("metrics.py", "PCC ham değerler üzerinden ve düzleştirilmiş matriste; delta yok", 1),
  task("Beş soru cevaplandı", null),
  task("Model bir kontrol hücresini perturbe hücreye nasıl dönüştürüyor? (tek cümle)", null, 1),
  task("Bir hücrede protein yoksa ne olur? (iki girdi zorunlu)", null, 1),
  task("Donör bilgisi modele nereden girebilir?", null, 1),
  task("Adversarial hizalama ne işe yarıyor, yerine ne konabilir (PoE/MoE, kontrastif)?", null, 1),
  task("Makaledeki değerlendirme neden iyimser?", null, 1),
  note("Bitti sayılır", "Biri MultiPert'i 3 dakikada şema üzerinden anlatabiliyor ve zayıf noktaları sayabiliyor."),
  note("Teslim", "research/…/multipert_mimari.md"),
);

// ---------- 2 ----------
S.push(...section(2, "COVID verisini hazırlamak", "Zhang vd. 2023: 6 donör × gün 0/2/10/28; CITE-seq (RNA+ADT) ve ASAP-seq (ATAC+ADT) farklı hücrelerde, köprü 173 ortak ADT."));
S.push(
  task("Veriyi indir (Wi-Fi'da)", "python scripts/covid/01_download.py"),
  task("PBMC_vaccine_CITE.rds (1,6 GB) ve PBMC_vaccine_ASAP.rds (4,7 GB) indi, MD5 \"OK\"", null, 1),
  task("İçeriği incele", "python scripts/covid/02_inspect_rds.py <dosya>"),
  task("Assay adları not edildi", "CITE: RNA, ADT … / ASAP: ADT, peaks/ATAC, GeneActivity?", 1),
  task("Metadata sütunları bulundu", "donör, gün (timepoint), hücre tipi; iki dosyada da", 1),
  task("h5ad'e dönüştür", "python scripts/covid/03_convert.py … --assays …"),
  task("CITE → RNA + ADT, ASAP → ADT + ATAC dosyaları oluştu", null, 1),
  task("py8rds okuyamazsa B planı: readseurat; o da olmazsa Colab'de tek seferlik dönüşüm", null, 1),
  task("config.json hazır", "scripts/covid/config.example.json kopyalanıp sütun adları dolduruldu"),
  task("CITE ve ASAP hücre tipi adları karşılaştırıldı, farklıysa cell_type_map ile eşlendi", null, 1),
  task("Veri özeti çıkarıldı", null),
  task("Donör × gün × hücre tipi hücre sayısı tablosu (iki assay için ayrı)", null, 1),
  task("Az hücreli (<10) gruplar işaretlendi", null, 1),
  task("Gün etkisinin büyük olduğu hücre tipleri not edildi", "(ör. aktive CD8 T, gün 28)", 1),
  note("Bitti sayılır", "04_run_lodo.py config.json ile hatasız açılıyor; veri özeti tablosu repoda."),
  note("Teslim", "research/…/covid_veri_yapisi.md + özet tablo"),
);

// ---------- 3 ----------
S.push(...section(3, "İlk sonuçlar: LODO baseline'ları", "5 donörle eğit, 6.'nın gün 2/10/28 profilini tahmin et. Bu tablo, her modelin geçmesi gereken çıtayı gösterir."));
S.push(
  task("Baseline'ları çalıştır", "python scripts/covid/04_run_lodo.py --config scripts/covid/config.json --strict"),
  task("6 fold tamamlandı, results/covid_lodo/ altında summary.csv ve mse_top20_by_day.csv var", null, 1),
  task("Sonuç tablosu hazırlandı", "model × modalite (RNA, CITE-ADT, ATAC, ASAP-ADT) × gün"),
  task("Donör-farkında modeller (ContextKNN, ContextRidge) PerturbationMean'i geçiyor mu?", null, 1),
  task("Fold'lar arası varyans gösterildi (6 donör az, gürültü önemli)", null, 1),
  task("Hücre tipi bazında kırılım", null, 1),
  task("Yorum yazıldı", "donörler arası cevap farkı ölçüm gürültüsünden büyük mü?"),
  note("Bitti sayılır", "Hocaya gösterilebilecek tek bir tablo + 3–4 cümlelik yorum."),
);

// ---------- 4 ----------
S.push(...section(4, "MultiPert'i çalıştırmak ve yeniden skorlamak", "Makaledeki sonuçları üretip bizim delta metrikleriyle karşılaştırmak."));
S.push(
  task("PyTorch kuruldu (Wi-Fi'da)", "CPU sürümü; okul PC'sinde/RTX 5070'te cu128 sürümü"),
  task("Orijinal haliyle çalıştırıldı", "external/MultiPert/code/main.py, Papalexi arrayed verisi (repo ile geliyor)"),
  task("Eğitim süresi ve donanım not edildi", null, 1),
  task("metrics_rna.csv / metrics_adt.csv makaledeki THP-1 sayılarıyla karşılaştırıldı", null, 1),
  task("Yeniden skorlandı", "tahminler pertbench/external.py ile delta metrikleri"),
  task("Aynı test hücrelerinde PerturbationMean baseline'ı ile kıyas", null, 1),
  task("\"Makaledeki PCC → bizim pearson_delta\" farkı tabloya döküldü", null, 1),
  note("Bitti sayılır", "Makale metriği ve bizim metrik yan yana; MultiPert basit baseline'ı geçiyor mu sorusunun cevabı var."),
);

// ---------- 5 ----------
S.push(...section(5, "Entegrasyon yöntemleri (Fu vd. 2025)", "MultiPert'in yeni omurgasını seçmek: CITE ve ASAP hücrelerini ortak bir uzaya taşıyacak yöntem."));
S.push(
  task("Makale okundu", "Fu vd., Nature Methods 2025, 22:2437–2448"),
  task("Mosaic RNA+ADT ve RNA+ATAC sonuçları (bizim COVID senaryosu)", null, 1),
  task("Diagonal RNA+ATAC sonuçları (sonraki nöroblastom verisi için)", null, 1),
  task("Kullanılan metrikler ve Supplementary'deki yöntem ayarları", null, 1),
  task("Metrik paketi ve pipeline'ın nerede olduğu bulundu", null, 1),
  task("Kısa liste ve uygulama kartları", "MIDAS, MultiVI, totalVI (GLUE sonraki veri için)"),
  task("Her biri için: kurulum, girdi formatı (h5ad/MuData), batch nasıl verilir, GPU/RAM, resmi örnek kod", null, 1),
  task("Hangisi köprü modalite (ADT) senaryosunu doğrudan destekliyor?", null, 1),
  task("İç toplantıda 1 yöntem seçildi", null),
  task("Seçilen yöntem COVID'de çalıştırıldı", "batch = assay (CITE/ASAP), donör DEĞİL"),
  task("Gerekirse alt örnekleme (donör × gün × hücre tipi başına sabit hücre) veya Kaggle GPU", null, 1),
  task("Ölçüldü", null),
  task("Modalite hizalama (CITE ve ASAP hücreleri karışıyor mu, hücre tipleri ayrışıyor mu)", null, 1),
  task("Modaliteler arası imputasyon (CITE hücrelerinden ATAC, ASAP hücrelerinden RNA)", null, 1),
  task("Donör korunumu (embedding'den donör etiketi ne kadar tahmin edilebiliyor)", null, 1),
  note("Teslim", "research/…/fu2025_kisa_liste.md, research/…/yontem_kartlari.md, results/integration/"),
);

// ---------- 6 ----------
S.push(...section(6, "Donör temsili ve perturbation modülü tasarımı", "Eşli hücre olmadan, görülmemiş donörün cevabını öğrenecek modülün tasarımı."));
S.push(
  task("Literatür tarandı: mevcut yöntemler donörü nasıl temsil ediyor?", null),
  task("CellFlow (kontrol ortalaması), CPA/biolord (kategorik kovaryat), scGen/scPILOT (latent aritmetik/OT), MultiCPA (Product of Experts)", null, 1),
  task("Hangisi görülmemiş donöre genellenebilir?", null, 1),
  task("Eşleşmesiz öğrenme seçenekleri karşılaştırıldı", "MMD kaybı, optimal transport, flow matching"),
  task("Sadece 6 donör varken hangisi mantıklı? (aşırı öğrenme riski)", null, 1),
  task("Tasarım dokümanı yazıldı", "girdiler, donör embedding'i, kayıp fonksiyonu, eğitim döngüsü, sözde kod"),
  task("MultiPert'in dikkat bloğu nasıl yeniden kullanılacak?", null, 1),
  note("Teslim", "research/…/donor_temsili.md, research/ortak/model_tasarimi_v1.md"),
);

// ---------- 7 ----------
S.push(...section(7, "Geliştirilmiş MultiPert prototipi", "Entegrasyon omurgası + donör koşullu perturbation modülü; COVID'de LODO."));
S.push(
  task("Omurga latent'i hazır", "seçilen entegrasyon yönteminden her hücre için ortak latent"),
  task("Donör embedding'i", "donörün baseline (gün 0) latent dağılımından: önce ortalama, sonra set encoder"),
  task("Perturbation modülü", "latent'te: baseline + donör + gün → tedavi sonrası dağılım"),
  task("Decoder'lar ile RNA, ADT ve ATAC'a geri dönüş", null),
  task("LODO 6 fold çalıştırıldı", null),
  task("Karşılaştırma tablosu: prototip vs MultiPert vs baseline'lar", null),
  note("B planı", "Prototip yetişmezse hocaya tasarım + baseline + entegrasyon sonucuyla gidilir."),
);

// ---------- 8 ----------
S.push(...section(8, "Değerlendirme altyapısı", "Herkesin aynı ölçütle karşılaştırılması."));
S.push(
  task("pertbench'e dağılım metrikleri eklendi", "MMD, energy distance (sentetik veriyle test)"),
  task("Donör korunumu metriği tanımlandı ve eklendi", null),
  task("Sonuçlar hücre tipi ve gün bazında raporlanıyor", null),
  task("Tüm deneyler sabit seed ile; derin modeller için birden fazla seed", null),
);

// ---------- 9 ----------
S.push(...section(9, "Toplantılar ve teslim", "Sprintin kapanışı."));
S.push(
  task("İç toplantı (1. hafta sonu, 30 dk)", "herkes 5 dk anlatır"),
  task("Entegrasyon yöntemi seçildi", null, 1),
  task("Perturbation modülü tasarımı seçildi", null, 1),
  task("Kararlar docs/ altına yazıldı", null, 1),
  task("Sonuç notu", "docs/sonuclar_sprint1.md: tablolar, şekiller, yorumlar"),
  task("Sunum (10 dk) hazır", "MultiPert analizi · COVID verisi + LODO tablosu · entegrasyon sonucu · mimari ve prototip"),
  task("Hoca görüşmesi yapıldı", null),
  task("Görüşme notları ve yeni kararlar docs/ altına yazıldı", null, 1),
);

S.push(new Paragraph({ spacing: { before: 300 },
  children: [new TextRun({ text: "Kaynak: github.com/Atytmr07/perturbation-prediction · docs/10_roadmap_gorev_paylasimi.md", font: FONT, size: 16, color: MUTED })] }));

const doc = new Document({
  creator: "Emre Atay Tümer",
  title: "Yapılacaklar: 2 Haftalık Sprint",
  styles: {
    default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: ACCENT, font: FONT }, paragraph: { outlineLevel: 0 } },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "7F7F7F", font: FONT })] })] }) },
    children: S,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "..", "docs", "Yapilacaklar_Sprint1.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote", out, buf.length, "bytes");
});
