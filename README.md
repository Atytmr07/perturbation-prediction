# pertubation-prediction

Bitirme projesi: donör-farkında, çok modaliteli tek hücre perturbation cevabı tahmini.

| Klasör | İçerik |
|---|---|
| `docs/01_literatur_taramasi.md` | MultiPert, MultiFlow ve alanın haritası; boşluklar |
| `docs/02_veri_setleri.md` | Multimodal ve çok donörlü veri setleri, erişim |
| `docs/03_arastirma_plani.md` | Problem tanımı, araştırma soruları, ön sonuçlar, takvim |
| `docs/04_hocaya_email_taslagi.md` | Hilal Hoca'ya yanıt taslağı |
| `pertbench/` | Benchmark paketi |
| `scripts/` | Veri indirme ve benchmark çalıştırma |
| `results/` | Özet tablolar (`summary.csv`, `skill_vs_PerturbationMean.csv`) |

## Kurulum

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

## Çalıştırma

```bash
.venv/Scripts/python -m pytest -q tests
.venv/Scripts/python scripts/run_benchmark.py --dataset synthetic
.venv/Scripts/python scripts/download_data.py papalexi2021 frangieh2021_protein
.venv/Scripts/python scripts/run_benchmark.py --dataset papalexi2021
.venv/Scripts/python scripts/run_benchmark.py --dataset frangieh2021_protein --min-cells 20
```

Kendi h5ad dosyanız için:
```bash
.venv/Scripts/python scripts/run_benchmark.py --dataset h5ad --path data/x.h5ad --pert-key perturbation --control control --donor-key donor --cell-type-key cell_type
```

## pertbench tasarımı
- **Veri:** `PerturbData` hücre düzeyinde her modalite için bir matris tutar. `pseudobulk()` bunu `(perturbation, cell_type, donor)` koşullarının ortalamalarına indirger. Modeller bu düzeyde çalışıyor. GEARS, Ahlmann-Eltze ve OP3 de değerlendirmeyi bu düzeyde yapıyor.
- **Split'ler (`splits.py`):**
  - `random`
  - `unseen_perturbation`
  - `unseen_cell_type` (LOO)
  - `unseen_donor` (LOO, `k_shot` destekli)

  Kontroller her zaman eğitimde kalıyor. Yeni bir hastanın baseline örneğinin elimizde olduğunu varsayıyoruz.
- **Metrikler (`metrics.py`):** `pearson_delta`, `pearson_delta_top20`, `mse_top20`, `direction_acc_top20`, `cosine_delta`. Ham `pearson` yalnızca referans için raporlanıyor.
- **Modeller (`models.py`):** NoChange, GlobalMean, PerturbationMean, Additive, ContextKNN, ContextRidge, LinearEmbedding, CrossModal. Açıklamaları dosyanın başında.
- **Harici modeller (`external.py`):**
  1. `export_split` bir split'i hücre düzeyinde h5ad olarak yazar.
  2. Harici model kendi ortamında eğitilir ve tahminlerini CSV'ye yazar.
  3. `ExternalPredictions` bu CSV'yi okur ve aynı koddan geçirerek skorlar.
- **Sentetik veri (`synthetic.py`):** Bilinen bir donör × perturbation etkileşimi ve yalnızca proteinde görülen etkiler içerir. Modellerin bu sinyalleri yakalayıp yakalamadığını test etmeye yarar.

## Notlar
- Protein-only Frangieh verisinde yalnızca 20 özellik var, bu yüzden `*_top20` metrikleri tüm özelliklere eşit.
- `skill_vs_PerturbationMean`, hata oranını koşul başına hesaplayıp ortalıyor. Bu nedenle özet tablodaki ortalama MSE sıralamasından farklı çıkabilir: az sayıda büyük etkili perturbation ortalamayı domine ediyor.
