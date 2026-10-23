"""Show that MultiPert's DualFusionAttention output does not depend on the cell embedding.

nn.MultiheadAttention (batch_first=False) gets query/key/value of shape (1, B, E): sequence length 1.
Softmax over a single key is 1, so the output is out_proj(W_v @ perturbation) for every cell.
Channel attention is then a function of that output only, and there is no residual connection,
so decoder input -- and the prediction -- depends on the perturbation alone.

Also checks the released THP-1 predictions (results/multipert_original/predict.h5ad): the
within-perturbation spread of predicted cells is ~1e-5, i.e. one profile per perturbation.

    python scripts/multipert/06_attention_check.py
"""
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "external" / "MultiPert" / "code"))
from models import DualFusionAttention  # noqa: E402

torch.manual_seed(0)
att = DualFusionAttention(embed_dim=64).eval()
cells = torch.randn(5, 64) * 3
same_pert = torch.randn(1, 64).repeat(5, 1)
with torch.no_grad():
    out = att(cells, same_pert)
    out_shuffled = att(cells[torch.randperm(5)], same_pert)
print(f"different cells, same perturbation -> max output difference: {(out - out[0]).abs().max():.2e}")
print(f"shuffled cells -> max difference: {(out - out_shuffled).abs().max():.2e}")
with torch.no_grad():
    o2 = att(cells, torch.randn(5, 64))
print(f"different perturbations -> max output difference: {(o2 - o2[0]).abs().max():.2e}")

# Which modules does the reconstruction (MSE) loss actually train? Same wiring as trainer.py.
from models import (ZINBVAE, Autoencoder, Decoder, FusionNetwork,  # noqa: E402
                    PerturbationEncoder, SharedEncoder)
d_rna, d_adt, d_pert = 50, 4, 64
mods = {"rna_specific": ZINBVAE(d_rna, 32), "adt_specific": Autoencoder(d_adt, 32),
        "shared_rna": SharedEncoder(d_rna, 32), "shared_adt": SharedEncoder(d_adt, 32),
        "fusion": FusionNetwork(64, 32), "pert_enc_rna": PerturbationEncoder(d_pert, 64),
        "pert_enc_adt": PerturbationEncoder(d_pert, 64), "attention": DualFusionAttention(64),
        "decoder_rna": Decoder(64, d_rna), "decoder_adt": Decoder(64, d_adt)}
rna, adt, pert = torch.rand(16, d_rna), torch.rand(16, d_adt), torch.randn(16, d_pert)
rna_spec, _ = mods["rna_specific"].encode(rna)
adt_spec = mods["adt_specific"].encoder(adt)
fused = mods["fusion"](mods["shared_rna"](rna), mods["shared_adt"](adt))
out_rna = mods["decoder_rna"](mods["attention"](torch.cat((rna_spec, fused), 1), mods["pert_enc_rna"](pert)))
out_adt = mods["decoder_adt"](mods["attention"](torch.cat((adt_spec, fused), 1), mods["pert_enc_adt"](pert)))
(((out_rna - torch.rand_like(out_rna)) ** 2).mean() + ((out_adt - torch.rand_like(out_adt)) ** 2).mean()).backward()
print("gradient of the reconstruction loss per module (0 = never trained by it):")
for name, m in mods.items():
    g = sum(float(q.grad.abs().sum()) for q in m.parameters() if q.grad is not None)
    print(f"  {name:13s} {g:.2e}")

pred = ROOT / "results" / "multipert_original" / "predict.h5ad"
if pred.exists():
    import anndata as ad
    a = ad.read_h5ad(pred)
    X, P = np.asarray(a.X), a.obs["perturb"].astype(str).to_numpy()
    spread = max(float(X[P == p].std(0).max()) for p in np.unique(P))
    print(f"THP-1 predictions: {X.shape[0]} cells, {len(np.unique(P))} perturbations, "
          f"max within-perturbation std {spread:.1e}")
