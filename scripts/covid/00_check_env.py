"""Okul PC'sinde ortamı doğrula: GPU görünüyor mu, RTX 5070 (sm_120) için doğru PyTorch kurulu mu?

    python scripts/covid/00_check_env.py
"""

import importlib
import platform
import shutil

print("python   ", platform.python_version(), platform.system())
for mod in ["numpy", "pandas", "scipy", "anndata", "scanpy", "torch", "py8rds"]:
    try:
        m = importlib.import_module(mod)
        print(f"{mod:9s}", getattr(m, "__version__", "ok"))
    except Exception as e:  # noqa: BLE001
        print(f"{mod:9s} YOK ({e.__class__.__name__})")

try:
    import torch
    print("cuda     ", torch.cuda.is_available(), "| torch cuda build:", torch.version.cuda)
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        cap = torch.cuda.get_device_capability(0)
        print("gpu      ", name, "compute capability", cap)
        x = torch.randn(4096, 4096, device="cuda")
        print("matmul   ", float((x @ x).sum().cpu()) is not None, "(GPU üzerinde çalıştı)")
        if cap >= (12, 0) and (torch.version.cuda or "0") < "12.8":
            print("UYARI: RTX 50xx için CUDA 12.8+ ile derlenmiş PyTorch gerekir (cu128).")
except Exception as e:  # noqa: BLE001
    print("torch/GPU testi başarısız:", e)

total, used, free = shutil.disk_usage(".")
print(f"disk     boş {free / 1e9:.0f} GB (COVID verisi için ~20 GB gerekir)")
