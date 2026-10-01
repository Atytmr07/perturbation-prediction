# CLAUDE.md

Bu repo bir bitirme projesi: görülmemiş bir donörün multimodal (RNA + ATAC/ADT) perturbation cevabını, o donörün tedavi öncesi hücrelerinden tahmin etmek. Tüm bağlam, kararlar ve hocanın istekleri:

@PROJE_BAGLAMI.md

Kısa kurallar:
- Kullanıcılarla Türkçe konuş.
- R kullanma; her şey Python.
- Test donörü ön işlemeye sızmamalı (özellik seçimi/normalizasyon sadece eğitim donörlerinden).
- Sonuçları delta metrikleriyle ve `PerturbationMean` baseline'ına karşı raporla.
- Entegrasyon yöntemlerine donörü "batch" olarak verme.
- Testler: `python -m pytest -q tests`.
