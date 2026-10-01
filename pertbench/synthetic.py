"""Synthetic multi-modal, multi-donor perturbation data with known ground truth.

Used for tests and for sanity-checking that a model can exploit donor structure
before spending compute on real data. The generative story:

  programs      K latent gene programs, gene loadings W (K x G)
  perturbation  sparse program effect e_p, plus direct knock-down of its target gene
  cell type     program sensitivity s_ct (K), baseline expression mu_ct
  donor         latent genotype z_d (r); it shifts baseline expression (mu_d = C z_d)
                AND modulates program sensitivity (1 + B z_d). The second part is
                a donor x perturbation interaction that no additive model captures,
                but which is partly recoverable from the donor's control profile.
  protein       linear readout of a subset of genes + a protein-only effect of some
                perturbations (post-transcriptional), so RNA alone is not sufficient.
  atac          separate program loadings; chromatin shift is ~ program effect.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pertbench.data import PerturbData


def make_synthetic(
    n_genes: int = 200,
    n_proteins: int = 30,
    n_peaks: int = 100,
    n_programs: int = 10,
    n_perts: int = 30,
    n_cell_types: int = 3,
    n_donors: int = 8,
    donor_dim: int = 3,
    cells_per_condition: int = 30,
    donor_interaction: float = 0.6,
    protein_only_frac: float = 0.3,
    noise: float = 0.4,
    seed: int = 0,
) -> PerturbData:
    rng = np.random.default_rng(seed)
    K, G = n_programs, n_genes

    W = rng.normal(0, 1, (K, G)) * (rng.random((K, G)) < 0.15)
    W_atac = rng.normal(0, 1, (K, n_peaks)) * (rng.random((K, n_peaks)) < 0.2)
    prot_genes = rng.choice(G, n_proteins, replace=False)
    prot_gain = rng.uniform(0.5, 1.5, n_proteins)

    mu_ct = rng.normal(2.0, 0.5, (n_cell_types, G))
    s_ct = rng.uniform(0.5, 1.5, (n_cell_types, K))

    z = rng.normal(0, 1, (n_donors, donor_dim))
    C = rng.normal(0, 0.3, (donor_dim, G))
    B = rng.normal(0, donor_interaction / np.sqrt(donor_dim), (K, donor_dim))
    donor_sens = 1.0 + z @ B.T                               # (n_donors, K)

    in_program = np.flatnonzero((W != 0).sum(axis=0) > 0)
    targets = rng.choice(in_program, n_perts, replace=False)
    # Knocking out a gene perturbs the programs it belongs to (so gene embeddings carry
    # information about unseen perturbations), plus a perturbation-specific component.
    E = -W[:, targets].T * 1.5
    for p in range(n_perts):
        idx = rng.choice(K, rng.integers(0, 2), replace=False)
        E[p, idx] += rng.normal(0, 1.0, len(idx))
    prot_only = np.zeros((n_perts, n_proteins))
    for p in rng.choice(n_perts, int(protein_only_frac * n_perts), replace=False):
        j = rng.choice(n_proteins, rng.integers(1, 4), replace=False)
        prot_only[p, j] = rng.normal(0, 1.5, len(j))

    pert_names = ["control"] + [f"KO_g{t}" for t in targets]
    rna, prot, atac, obs = [], [], [], []
    for ct in range(n_cell_types):
        for d in range(n_donors):
            base = mu_ct[ct] + z[d] @ C
            for pi, pname in enumerate(pert_names):
                n = cells_per_condition
                if pi == 0:
                    prog, direct, pextra = np.zeros(K), np.zeros(G), np.zeros(n_proteins)
                else:
                    p = pi - 1
                    prog = E[p] * s_ct[ct] * donor_sens[d]
                    direct = np.zeros(G)
                    direct[targets[p]] = -1.5                   # knock-down of the target gene
                    pextra = prot_only[p]
                state = rng.normal(0, 0.3, (n, K))              # cell-to-cell program variability
                x = base + (prog + state) @ W + direct + rng.normal(0, noise, (n, G))
                y = x[:, prot_genes] * prot_gain + pextra + rng.normal(0, noise, (n, n_proteins))
                a = (prog + state) @ W_atac * 0.8 + rng.normal(0, noise, (n, n_peaks))
                rna.append(x); prot.append(y); atac.append(a)
                obs += [(pname, f"ct{ct}", f"donor{d}")] * n

    obs = pd.DataFrame(obs, columns=["perturbation", "cell_type", "donor"])
    X = {"rna": np.vstack(rna).astype(np.float32),
         "protein": np.vstack(prot).astype(np.float32),
         "atac": np.vstack(atac).astype(np.float32)}
    var = {"rna": [f"g{i}" for i in range(G)],
           "protein": [f"p_g{g}" for g in prot_genes],
           "atac": [f"peak{i}" for i in range(n_peaks)]}
    meta = pd.DataFrame({"perturbation": pert_names[1:], "target_gene": [f"g{t}" for t in targets]})
    return PerturbData(X=X, obs=obs, var=var, pert_meta=meta)
