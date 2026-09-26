"""
scripts/build_canonical.py
--------------------------
Convenience alias for:
  python -m src.preprocessing.build_canonical_dataset

Usage
-----
  python scripts/build_canonical.py
"""
from src.preprocessing.build_canonical_dataset import build_canonical_dataset
from src.config_loader import get_pipeline_config

if __name__ == "__main__":
    cfg  = get_pipeline_config()
    path = build_canonical_dataset(cfg)
    print(f"\nDone: {path}")
