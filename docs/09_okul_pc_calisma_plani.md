# Okul PC'si Çalışma Planı (RTX 5070, R yok)

*1 Ekim 2026. Her şey Python. R gerektiren yöntemler (Seurat v5 Bridge, Fu vd.'nin R tabanlı kısımları) bu plana dahil değil.*

## Adım 0: Projeyi okul PC'sine taşımak
- Önerim: Projeyi **özel bir GitHub reposuna** koyup okulda `git clone` ile çekmek. `data/`, `.venv/` ve büyük sonuç dosyaları zaten `.gitignore`'da.
- Alternatif: Klasörü USB ile taşımak. Veri dosyaları hariç birkaç MB tutuyor.

## Adım 1: Ortam kurulumu (~20 dk)
RTX 5070 Blackwell mimarisinde (sm_120). **CUDA 12.8 ile derlenmiş PyTorch şart**, daha eski sürümler GPU'yu görmez.

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install numpy pandas scipy anndata scanpy mudata pytest
pip install git+https://github.com/cellgeni/py8rds.git
python scripts/covid/00_check_env.py
python -m pytest -q tests
```

**Kontrol:** `00_check_env.py` çıktısında `cuda True` ve `compute capability (12, 0)` görünmeli. Testlerin 12'si de geçmeli.

## Adım 2: COVID verisi (Zhang vd. 2023): indir → incele → dönüştür

| Komut | Ne yapar | Süre / kaynak |
|---|---|---|
| `python scripts/covid/01_download.py` | CITE (1,6 GB) + ASAP (4,7 GB) Seurat dosyalarını Zenodo'dan indirir, MD5 kontrol eder, yarım kalırsa devam eder | İnternete bağlı |
| `python scripts/covid/02_inspect_rds.py data/covid/PBMC_vaccine_CITE.rds` | R olmadan dosyanın içindeki assay'leri (RNA, ADT…) ve metadata sütunlarını (donör, gün, hücre tipi) listeler | Birkaç dk. RAM ≈ dosya boyutunun 3–4 katı |
| `python scripts/covid/02_inspect_rds.py data/covid/PBMC_vaccine_ASAP.rds` | Aynısı ASAP için. ATAC assay'inin adına bak (`peaks`, `ATAC` veya `GeneActivity`) | 4,7 GB → ~15–20 GB RAM gerekebilir |
| `python scripts/covid/03_convert.py data/covid/PBMC_vaccine_CITE.rds --assays RNA ADT` | Her assay'i ayrı bir h5ad'e yazar | |
| `python scripts/covid/03_convert.py data/covid/PBMC_vaccine_ASAP.rds --assays ADT peaks` | Assay adlarını inceleme çıktısına göre düzelt | |

**Sonra:** `scripts/covid/config.example.json` dosyasını `config.json` olarak kopyala. Donör, gün ve hücre tipi sütun adlarını inceleme çıktısından doldur. İki assay'deki hücre tipi adları farklıysa `cell_type_map` ile eşle.

**Risk:** `py8rds` Seurat nesnelerinin çoğunu okuyabiliyor ama her versiyonu garanti etmiyor. Okuyamazsa yedek araç `pip install readseurat` (`readseurat.read_seurat(...)`). O da olmazsa, dönüşümü bir kez Colab'de yaparız. Bu durumda R'ı bizim makinelere kurmamız gerekmez.

## Adım 3: İlk sonuçlar, leave-one-donor-out baseline'ları (CPU, dakikalar)

```bash
python scripts/covid/04_run_lodo.py --config scripts/covid/config.json
python scripts/covid/04_run_lodo.py --config scripts/covid/config.json --strict
```

- Script 6 fold çalıştırıyor: her seferinde 5 donörle eğitip 6. donörün gün 2, 10 ve 28 profilini tahmin ediyor.
- Tahmin edilen modaliteler RNA, CITE-ADT, ATAC ve ASAP-ADT. Hepsi donör × gün × hücre tipi pseudobulk düzeyinde.
- `--strict` seçeneği özellik seçimini sadece eğitim donörleriyle yapıyor, böylece test donörü ön işlemeye sızmıyor. Raporda bu sürümün sonuçları kullanılmalı.
- Çıktılar `results/covid_lodo/` altına yazılıyor: `summary.csv`, `mse_top20_by_day.csv` ve per-condition sonuçlar.

**Bu adım şu soruya cevap veriyor:** "Diğer 5 donörün ortalama değişimi" (`PerturbationMean`) yeni donörü ne kadar iyi tahmin ediyor, ve donörün baseline'ını kullanan modeller (`ContextKNN`, `ContextRidge`) bunu geçebiliyor mu? MultiPert ve entegrasyon modellerinin geçmesi gereken çıta bu.

*Not:* `LinearEmbedding` bu veride anlamsız, çünkü perturbation'lar gen değil. GlobalMean ile aynı sonucu verir, raporda göz ardı edilebilir.

## Adım 4: İki iz (2–3 hafta)

### İz A: MultiPert (Berk, Alperen + Atay)
| # | İş | GPU? |
|---|---|---|
| A1 | MultiPert'i orijinal haliyle çalıştır: `external/MultiPert/code/main.py` (repo Papalexi arrayed verisiyle geliyor). Makaledeki THP-1 sayılarını yeniden üret | Evet, ama küçük |
| A2 | MultiPert tahminlerini pertbench delta metrikleriyle yeniden skorla (`pertbench/external.py`). Makaledeki "PCC 0,88" bizim metrikle kaça düşüyor? | Hayır |
| A3 | MultiPert'i donör split'ine uyarla: donör içi eşleşme, eğitim donörlerinde HVG seçimi. Önce Lawlor/Papalexi gibi eşli RNA+protein verisinde dene | Evet |
| A4 | Dağılım düzeyinde versiyon: hücre eşleşmesi yok. Baseline latent dağılımı + donör embedding'i → tedavi sonrası dağılım. Kayıp: MMD veya OT | Evet |

### İz B: Entegrasyon benchmark'ı (1 kişi, Fu vd. 2025)
| # | İş | Kurulum |
|---|---|---|
| B1 | Fu vd.: mosaic (RNA+ADT, RNA+ATAC) ve diagonal bölümlerini, metrikleri ve Supplementary'deki ayarları oku | – |
| B2 | Python'da çalışan aday yöntemleri COVID verisinde çalıştır. CITE + ASAP, köprü ADT: **MIDAS**, **MultiVI** (scvi-tools), **GLUE** (scglue), **totalVI** (sadece CITE için) | `pip install scvi-tools scglue`. MIDAS için repodaki kurulum talimatı izlenecek |
| B3 | Fu vd.'nin metriklerine ek olarak **donör korunumu**: embedding'den donör etiketi ne kadar iyi tahmin ediliyor. Ayrıca **modalite imputasyonu**: CITE hücrelerinden ATAC, ASAP hücrelerinden RNA | – |
| B4 | En iyi 1–2 omurgayı İz A'ya teslim et: embedding + decoder'lar | – |

**Önemli uyarı (İz B):** Yöntemlere batch olarak **assay** (CITE/ASAP) veya kütüphane verilmeli, **donör verilmemeli**. Donör verilirse, korumak istediğimiz donör farkını siler.

## Hocayla bir sonraki toplantıya götürülecekler
1. COVID verisinin yapısı: hücre sayıları, donör × gün × hücre tipi tablosu, iki assay'in eşleşmesi.
2. Leave-one-donor-out baseline tablosu (Adım 3). İlk somut sayılar.
3. MultiPert'in yeniden üretimi ve bizim metriklerle yeniden skorlanmış hali (A1–A2).
4. Entegrasyon için kısa liste ve ilk karşılaştırma (B1–B2).
5. Önerilen mimari: entegrasyon omurgası + donör koşullu perturbation modülü (`08_iki_iz_plani.md`).

## Riskler
| Risk | Önlem |
|---|---|
| py8rds Seurat dosyasını okuyamaz | readseurat dene. Olmazsa Colab'de tek seferlik R dönüşümü |
| ASAP dosyası RAM'e sığmaz | Okul PC'sinin RAM'ini kontrol et. Gerekirse sadece ADT + gene activity assay'ini oku |
| 6 donör az, sonuçlar gürültülü | Hücre tipi bazında raporla, fold'lar arası varyansı göster. Sonra nöroblastoma (22 hasta) geç |
| Aşı etkisi küçük alt popülasyonlarda (antijene özgü CD8 T) | Hücre tipi çözünürlüğünü ince tut. Gün 28 + CD8 alt tiplerine ayrıca bak |
