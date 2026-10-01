"""pertbench: a small, CPU-friendly benchmark for single-cell perturbation response prediction.

Focus: multi-modal readouts (RNA + protein / ATAC) and donor-level generalisation.
All models operate on condition-level pseudobulk profiles, which is what most
published evaluations (GEARS, Ahlmann-Eltze et al. 2025, OP3) actually score.
"""

from pertbench.data import PerturbData, ConditionTable, pseudobulk
from pertbench.synthetic import make_synthetic

__all__ = ["PerturbData", "ConditionTable", "pseudobulk", "make_synthetic"]
