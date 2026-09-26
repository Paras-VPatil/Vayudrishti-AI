"""
config_loader.py
----------------
Central utility to load pipeline_config.yaml and feature_config.yaml.
All modules should call get_pipeline_config() instead of reading YAML directly.
"""

from __future__ import annotations

import yaml
from pathlib import Path
from functools import lru_cache

# ── Default config path (relative to repo root) ─────────────
_PIPELINE_CONFIG_PATH = Path(__file__).parent.parent / "configs" / "pipeline_config.yaml"
_FEATURE_CONFIG_PATH  = Path(__file__).parent.parent / "configs" / "feature_config.yaml"


@lru_cache(maxsize=1)
def get_pipeline_config(config_path: str | None = None) -> dict:
    """
    Load and cache pipeline_config.yaml.

    Parameters
    ----------
    config_path : str, optional
        Override path to a YAML config file. Useful in tests.

    Returns
    -------
    dict
        Parsed YAML as a Python dictionary.
    """
    path = Path(config_path) if config_path else _PIPELINE_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Pipeline config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def get_feature_config(config_path: str | None = None) -> dict:
    """
    Load and cache feature_config.yaml.

    Parameters
    ----------
    config_path : str, optional
        Override path to a YAML config file. Useful in tests.

    Returns
    -------
    dict
        Parsed YAML as a Python dictionary.
    """
    path = Path(config_path) if config_path else _FEATURE_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Feature config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_paths(config: dict | None = None) -> dict:
    """
    Convenience: return the 'paths' block from pipeline config.

    Returns
    -------
    dict
        Path strings keyed by role (raw_ground, interim, processed, …).
    """
    cfg = config or get_pipeline_config()
    return cfg["paths"]


def get_bbox(config: dict | None = None) -> dict:
    """
    Convenience: return the bounding box dict.

    Returns
    -------
    dict
        Keys: lat_min, lat_max, lon_min, lon_max (all floats).
    """
    cfg = config or get_pipeline_config()
    return cfg["bbox"]


def get_physical_bounds(config: dict | None = None) -> dict:
    """
    Return the physical_bounds block used for QC in cleaning modules.
    """
    cfg = config or get_pipeline_config()
    return cfg.get("physical_bounds", {})
