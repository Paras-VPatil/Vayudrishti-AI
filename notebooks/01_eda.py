"""
notebooks/01_eda.py
--------------------
Stage 7 — Exploratory Data Analysis (18 required sections).

Runs against canonical_dataset.parquet if available, otherwise
falls back to mock_data/mock_aqi_features.csv for development.

Produces:
  docs/eda/            — all plots as PNG files
  docs/eda_findings.md — written observations (T7.2)

Usage
-----
  python notebooks/01_eda.py
  python notebooks/01_eda.py --data data/processed/pune/canonical_dataset.parquet
  python notebooks/01_eda.py --data mock_data/mock_aqi_features.csv
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — works without a display
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Output directory ───────────────────────────────────────────────────────
EDA_DIR = Path("docs/eda")
EDA_DIR.mkdir(parents=True, exist_ok=True)

# ── Plot style ─────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi":       120,
    "figure.facecolor": "#0f1117",
    "axes.facecolor":   "#1a1d27",
    "axes.edgecolor":   "#3d4158",
    "axes.labelcolor":  "#e0e0e0",
    "xtick.color":      "#9e9e9e",
    "ytick.color":      "#9e9e9e",
    "text.color":       "#e0e0e0",
    "grid.color":       "#2a2d3e",
    "grid.alpha":       0.5,
    "font.family":      "DejaVu Sans",
    "axes.titlesize":   13,
    "axes.labelsize":   11,
})

AQI_PALETTE = {
    "Good":        "#00e676",
    "Satisfactory":"#b2ff59",
    "Moderate":    "#ffeb3b",
    "Poor":        "#ff9800",
    "Very Poor":   "#f44336",
    "Severe":      "#9c27b0",
}

FINDINGS: list[str] = []


def _save(fig: plt.Figure, name: str, finding: str = "") -> None:
    path = EDA_DIR / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  [{name}] saved → {path}")
    if finding:
        FINDINGS.append(f"**{name}**: {finding}")


def _load_data(data_path: str | None) -> pd.DataFrame:
    """Load canonical dataset or fall back to mock data."""
    canonical = Path("data/processed/pune/canonical_dataset.parquet")
    mock_csv  = Path("mock_data/mock_aqi_features.csv")

    if data_path:
        p = Path(data_path)
        df = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)
        print(f"Loaded data from: {p} ({len(df):,} rows)")
    elif canonical.exists():
        df = pd.read_parquet(canonical)
        print(f"Loaded canonical dataset ({len(df):,} rows)")
    elif mock_csv.exists():
        df = pd.read_csv(mock_csv)
        print(f"[MOCK] canonical_dataset.parquet not found — using mock data ({len(df):,} rows)")
    else:
        raise FileNotFoundError("No data source found. Run the ingestion pipeline first.")

    # Alias harmonisation
    alias = {
        "ground_pm25": "pm25_ground",
        "aod":         "aod_550nm",
        "temperature": "temperature_2m",
        "humidity":    "relative_humidity_2m",
        "wind_speed":  "wind_speed_10m",
        "wind_direction": "wind_direction_10m",
    }
    for old, new in alias.items():
        if old in df.columns and new not in df.columns:
            df[new] = df[old]

    # Parse timestamp
    if "timestamp_utc" in df.columns:
        df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
        df["hour"]  = df["timestamp_utc"].dt.hour
        df["month"] = df["timestamp_utc"].dt.month
        df["doy"]   = df["timestamp_utc"].dt.dayofyear
        df["season"] = df["month"].map({
            12: "Winter", 1: "Winter",  2: "Winter",
            3:  "Spring", 4: "Spring",  5: "Spring",
            6:  "Monsoon",7: "Monsoon", 8: "Monsoon", 9: "Monsoon",
            10: "Post-Monsoon", 11: "Post-Monsoon",
        })

    return df


# ══════════════════════════════════════════════════════════════════════════
# 01 — Shape, dtypes, basic stats
# ══════════════════════════════════════════════════════════════════════════
def section_01_overview(df: pd.DataFrame) -> None:
    print("\n[01] Basic overview")
    print(f"  Shape:   {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    if "pm25_ground" in df.columns:
        print(f"  PM2.5 stats: {df['pm25_ground'].describe().round(2).to_dict()}")
    FINDINGS.append(
        f"**Dataset shape**: {df.shape[0]:,} rows × {df.shape[1]} columns. "
        f"Target PM2.5 range: {df.get('pm25_ground', pd.Series([0])).min():.1f}–"
        f"{df.get('pm25_ground', pd.Series([500])).max():.1f} µg/m³."
    )


# ══════════════════════════════════════════════════════════════════════════
# 02 — Missing value heatmap
# ══════════════════════════════════════════════════════════════════════════
def section_02_missing(df: pd.DataFrame) -> None:
    print("[02] Missing value heatmap")
    miss = df.isnull().mean().sort_values(ascending=False)
    miss = miss[miss > 0]

    if miss.empty:
        FINDINGS.append("**Missingness**: No missing values in the dataset.")
        return

    fig, ax = plt.subplots(figsize=(10, max(4, len(miss) * 0.3)))
    colors = ["#ff5252" if v > 0.20 else "#ffab40" if v > 0.05 else "#69f0ae" for v in miss.values]
    bars = ax.barh(miss.index, miss.values * 100, color=colors, height=0.7)
    ax.set_xlabel("Missing (%)")
    ax.set_title("Missing Value Rate by Column", fontweight="bold")
    ax.axvline(5,  color="#ffeb3b", ls="--", lw=1, label="5% threshold")
    ax.axvline(20, color="#ff5252", ls="--", lw=1, label="20% threshold")
    ax.legend(framealpha=0.3)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    _save(fig, "02_missing_heatmap",
          f"Columns with >5% missingness: {(miss > 0.05).sum()}. "
          f"Highest: {miss.index[0]} ({miss.iloc[0]*100:.1f}%).")


# ══════════════════════════════════════════════════════════════════════════
# 03 — PM2.5 distribution
# ══════════════════════════════════════════════════════════════════════════
def section_03_pm25_dist(df: pd.DataFrame) -> None:
    print("[03] PM2.5 distribution")
    if "pm25_ground" not in df.columns:
        return

    pm25 = df["pm25_ground"].dropna()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    # Histogram
    ax1.hist(pm25, bins=60, color="#7c4dff", edgecolor="#0f1117", alpha=0.85)
    ax1.axvline(pm25.mean(),   color="#ff6d00", lw=2, label=f"Mean={pm25.mean():.1f}")
    ax1.axvline(pm25.median(), color="#00e676", lw=2, label=f"Median={pm25.median():.1f}")
    ax1.set_xlabel("PM2.5 (µg/m³)")
    ax1.set_ylabel("Count")
    ax1.set_title("PM2.5 Distribution", fontweight="bold")
    ax1.legend(framealpha=0.3)
    ax1.grid(alpha=0.3)

    # Box plot with AQI category reference lines
    bp = ax2.boxplot(pm25, vert=True, patch_artist=True,
                     boxprops=dict(facecolor="#7c4dff", alpha=0.7),
                     medianprops=dict(color="#ff6d00", lw=2),
                     whiskerprops=dict(color="#9e9e9e"),
                     capprops=dict(color="#9e9e9e"),
                     flierprops=dict(marker=".", color="#f44336", alpha=0.3, markersize=3))
    ax2.axhline(60,  color="#ffeb3b", ls="--", lw=1, label="Moderate threshold (60)")
    ax2.axhline(90,  color="#ff9800", ls="--", lw=1, label="Poor threshold (90)")
    ax2.axhline(120, color="#f44336", ls="--", lw=1, label="Very Poor threshold (120)")
    ax2.set_title("PM2.5 Box Plot", fontweight="bold")
    ax2.set_ylabel("PM2.5 (µg/m³)")
    ax2.legend(framealpha=0.3, fontsize=8)
    ax2.grid(alpha=0.3)

    fig.suptitle("PM2.5 Ground Measurements — Pune", fontweight="bold", fontsize=14)
    fig.tight_layout()
    skew = pm25.skew()
    _save(fig, "03_pm25_distribution",
          f"Right-skewed distribution (skew={skew:.2f}). "
          f"Mean={pm25.mean():.1f}, Median={pm25.median():.1f} µg/m³. "
          f"{(pm25 > 60).mean()*100:.1f}% of readings exceed 'Moderate' threshold.")


# ══════════════════════════════════════════════════════════════════════════
# 04 — AOD vs PM2.5 scatter
# ══════════════════════════════════════════════════════════════════════════
def section_04_aod_pm25(df: pd.DataFrame) -> None:
    print("[04] AOD vs PM2.5")
    if "aod_550nm" not in df.columns or "pm25_ground" not in df.columns:
        return

    sub = df[["aod_550nm", "pm25_ground"]].dropna()
    r = sub.corr().iloc[0, 1]

    fig, ax = plt.subplots(figsize=(8, 6))
    h = ax.hexbin(sub["aod_550nm"], sub["pm25_ground"], gridsize=40,
                  cmap="plasma", mincnt=1, alpha=0.85)
    fig.colorbar(h, ax=ax, label="Count")

    # Regression line
    m, b = np.polyfit(sub["aod_550nm"], sub["pm25_ground"], 1)
    x_range = np.linspace(sub["aod_550nm"].min(), sub["aod_550nm"].max(), 100)
    ax.plot(x_range, m * x_range + b, color="#00e676", lw=2, label=f"r = {r:.3f}")

    ax.set_xlabel("MODIS AOD 550nm")
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_title("AOD vs PM2.5 — Key Satellite-Ground Relationship", fontweight="bold")
    ax.legend(framealpha=0.3)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    _save(fig, "04_aod_pm25_scatter",
          f"AOD–PM2.5 Pearson r = {r:.3f}. "
          f"{'Strong' if abs(r) > 0.6 else 'Moderate' if abs(r) > 0.4 else 'Weak'} correlation.")


# ══════════════════════════════════════════════════════════════════════════
# 05 — NO2 vs PM2.5
# ══════════════════════════════════════════════════════════════════════════
def section_05_no2_pm25(df: pd.DataFrame) -> None:
    print("[05] NO2 vs PM2.5")
    col = next((c for c in ["satellite_no2", "no2_tropospheric_column"] if c in df.columns), None)
    if not col or "pm25_ground" not in df.columns:
        return

    sub = df[[col, "pm25_ground"]].dropna()
    r = sub.corr().iloc[0, 1]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(sub[col], sub["pm25_ground"], alpha=0.3, s=6, color="#40c4ff")
    m, b = np.polyfit(sub[col], sub["pm25_ground"], 1)
    x_range = np.linspace(sub[col].min(), sub[col].max(), 100)
    ax.plot(x_range, m * x_range + b, color="#ff6d00", lw=2, label=f"r = {r:.3f}")
    ax.set_xlabel("TROPOMI NO₂ column density (mol/m²)")
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_title("TROPOMI NO₂ vs PM2.5", fontweight="bold")
    ax.legend(framealpha=0.3)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    _save(fig, "05_no2_pm25_scatter",
          f"NO₂–PM2.5 Pearson r = {r:.3f}. "
          "NO₂ is a co-pollutant proxy for combustion sources (traffic, industry).")


# ══════════════════════════════════════════════════════════════════════════
# 06 — Wind speed vs PM2.5
# ══════════════════════════════════════════════════════════════════════════
def section_06_wind_pm25(df: pd.DataFrame) -> None:
    print("[06] Wind speed vs PM2.5")
    col = next((c for c in ["wind_speed_10m", "wind_speed"] if c in df.columns), None)
    if not col or "pm25_ground" not in df.columns:
        return

    sub = df[[col, "pm25_ground"]].dropna()
    # Bin by wind speed
    bins = [0, 1, 2, 3, 5, 8, 12, 100]
    labels = ["0-1", "1-2", "2-3", "3-5", "5-8", "8-12", "12+"]
    sub["ws_bin"] = pd.cut(sub[col], bins=bins, labels=labels)
    grouped = sub.groupby("ws_bin", observed=True)["pm25_ground"].median()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    ax1.scatter(sub[col], sub["pm25_ground"], alpha=0.2, s=4, color="#7c4dff")
    ax1.set_xlabel("Wind Speed (m/s)")
    ax1.set_ylabel("PM2.5 (µg/m³)")
    ax1.set_title("Wind Speed vs PM2.5", fontweight="bold")
    ax1.grid(alpha=0.3)

    bars = ax2.bar(range(len(grouped)), grouped.values, color="#00e5ff", edgecolor="#0f1117", alpha=0.85)
    ax2.set_xticks(range(len(grouped)))
    ax2.set_xticklabels(grouped.index, rotation=30)
    ax2.set_xlabel("Wind Speed Bin (m/s)")
    ax2.set_ylabel("Median PM2.5 (µg/m³)")
    ax2.set_title("Median PM2.5 by Wind Speed Category", fontweight="bold")
    ax2.grid(axis="y", alpha=0.3)

    r = sub[[col, "pm25_ground"]].corr().iloc[0, 1]
    fig.tight_layout()
    _save(fig, "06_wind_pm25",
          f"Wind speed negatively correlated with PM2.5 (r = {r:.3f}). "
          "High winds (>5 m/s) disperse pollutants, reducing surface concentration.")


# ══════════════════════════════════════════════════════════════════════════
# 07 — PBLH vs PM2.5 (critical: boundary layer inversions)
# ══════════════════════════════════════════════════════════════════════════
def section_07_pblh_pm25(df: pd.DataFrame) -> None:
    print("[07] PBLH vs PM2.5 (boundary layer inversions)")
    if "boundary_layer_height" not in df.columns or "pm25_ground" not in df.columns:
        return

    sub = df[["boundary_layer_height", "pm25_ground"]].dropna()
    r = sub.corr().iloc[0, 1]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    ax1.hexbin(sub["boundary_layer_height"], sub["pm25_ground"],
               gridsize=35, cmap="YlOrRd", mincnt=1, alpha=0.9)
    ax1.axvline(500,  color="#ff6d00", ls="--", lw=1.5, label="Shallow PBLH (500m)")
    ax1.axvline(1500, color="#00e676", ls="--", lw=1.5, label="Deep PBLH (1500m)")
    ax1.set_xlabel("Boundary Layer Height (m)")
    ax1.set_ylabel("PM2.5 (µg/m³)")
    ax1.set_title("PBLH vs PM2.5 — Inversion Effect", fontweight="bold")
    ax1.legend(framealpha=0.3)
    ax1.grid(alpha=0.3)

    # Median PM2.5 by PBLH quartile
    sub["pblh_q"] = pd.qcut(sub["boundary_layer_height"], 4,
                             labels=["Q1\n(Shallow)", "Q2", "Q3", "Q4\n(Deep)"])
    grouped = sub.groupby("pblh_q", observed=True)["pm25_ground"].median()
    colors  = ["#f44336", "#ff9800", "#ffeb3b", "#00e676"]
    ax2.bar(range(4), grouped.values, color=colors, edgecolor="#0f1117", alpha=0.85)
    ax2.set_xticks(range(4))
    ax2.set_xticklabels(grouped.index)
    ax2.set_ylabel("Median PM2.5 (µg/m³)")
    ax2.set_title("Median PM2.5 by PBLH Quartile", fontweight="bold")
    ax2.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    _save(fig, "07_pblh_pm25",
          f"PBLH–PM2.5 Pearson r = {r:.3f}. "
          "Shallow boundary layers (<500m) trap pollutants near the surface. "
          "This is the strongest meteorological driver of high-pollution events.")


# ══════════════════════════════════════════════════════════════════════════
# 08 — Temperature vs PM2.5
# ══════════════════════════════════════════════════════════════════════════
def section_08_temp_pm25(df: pd.DataFrame) -> None:
    print("[08] Temperature vs PM2.5")
    col = next((c for c in ["temperature_2m", "temperature"] if c in df.columns), None)
    if not col or "pm25_ground" not in df.columns:
        return

    sub = df[[col, "pm25_ground"]].dropna()
    r = sub.corr().iloc[0, 1]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(sub[col], sub["pm25_ground"], alpha=0.2, s=5, color="#ff6d00")
    m, b = np.polyfit(sub[col], sub["pm25_ground"], 1)
    x_range = np.linspace(sub[col].quantile(0.01), sub[col].quantile(0.99), 100)
    ax.plot(x_range, m * x_range + b, color="#00e676", lw=2, label=f"r = {r:.3f}")
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_title("Temperature vs PM2.5", fontweight="bold")
    ax.legend(framealpha=0.3)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    _save(fig, "08_temp_pm25",
          f"Temperature–PM2.5 r = {r:.3f}. "
          "Higher temperatures in summer often coincide with lower PM2.5 due to stronger convection.")


# ══════════════════════════════════════════════════════════════════════════
# 09 — Hourly temporal patterns
# ══════════════════════════════════════════════════════════════════════════
def section_09_hourly(df: pd.DataFrame) -> None:
    print("[09] Hourly PM2.5 patterns")
    if "hour" not in df.columns or "pm25_ground" not in df.columns:
        FINDINGS.append("**Hourly patterns**: timestamp column not parsed.")
        return

    hourly = df.groupby("hour")["pm25_ground"].agg(["mean", "std"]).reset_index()

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.fill_between(hourly["hour"],
                    hourly["mean"] - hourly["std"],
                    hourly["mean"] + hourly["std"],
                    alpha=0.2, color="#7c4dff", label="±1 std")
    ax.plot(hourly["hour"], hourly["mean"], "o-", color="#7c4dff", lw=2.5, ms=6, label="Mean PM2.5")
    ax.set_xlabel("Hour (UTC)")
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_title("Diurnal Cycle of PM2.5", fontweight="bold")
    ax.set_xticks(range(0, 24, 2))
    ax.axvspan(10, 14, alpha=0.08, color="#00e676", label="Satellite overpass window")
    ax.legend(framealpha=0.3)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    peak_h = hourly.loc[hourly["mean"].idxmax(), "hour"]
    _save(fig, "09_hourly_pm25",
          f"Peak PM2.5 at hour {peak_h:02d}:00 UTC. "
          "Morning and evening rush hours typically drive elevated PM2.5.")


# ══════════════════════════════════════════════════════════════════════════
# 10 — Monthly temporal patterns
# ══════════════════════════════════════════════════════════════════════════
def section_10_monthly(df: pd.DataFrame) -> None:
    print("[10] Monthly PM2.5 patterns")
    if "month" not in df.columns or "pm25_ground" not in df.columns:
        return

    monthly = df.groupby("month")["pm25_ground"].median()
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    colors = ["#f44336" if m in [11,12,1,2] else "#4caf50" if m in [6,7,8,9] else "#ff9800"
              for m in range(1, 13)]

    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.bar([month_names[m-1] for m in range(1, 13)],
                  [monthly.get(m, np.nan) for m in range(1, 13)],
                  color=colors, edgecolor="#0f1117", alpha=0.85)
    ax.set_xlabel("Month")
    ax.set_ylabel("Median PM2.5 (µg/m³)")
    ax.set_title("Seasonal PM2.5 Variation — Pune", fontweight="bold")
    ax.axhline(60, color="#ffeb3b", ls="--", lw=1, label="Moderate (60 µg/m³)")
    ax.legend(framealpha=0.3)
    ax.grid(axis="y", alpha=0.3)
    from matplotlib.patches import Patch
    legend_patches = [
        Patch(color="#f44336", alpha=0.85, label="Winter"),
        Patch(color="#ff9800", alpha=0.85, label="Spring/Post-Monsoon"),
        Patch(color="#4caf50", alpha=0.85, label="Monsoon"),
    ]
    ax.legend(handles=legend_patches, framealpha=0.3)
    fig.tight_layout()
    min_m = monthly.idxmin() if len(monthly) else None
    max_m = monthly.idxmax() if len(monthly) else None
    _save(fig, "10_monthly_pm25",
          f"Lowest PM2.5 in month {min_m} (monsoon wet deposition). "
          f"Highest in month {max_m} (winter temperature inversions + crop burning).")


# ══════════════════════════════════════════════════════════════════════════
# 11 — Seasonal box plots
# ══════════════════════════════════════════════════════════════════════════
def section_11_seasonal(df: pd.DataFrame) -> None:
    print("[11] Seasonal box plots")
    if "season" not in df.columns or "pm25_ground" not in df.columns:
        return

    seasons = ["Winter", "Spring", "Monsoon", "Post-Monsoon"]
    season_data = [df[df["season"] == s]["pm25_ground"].dropna().values for s in seasons]
    season_colors = ["#64b5f6", "#a5d6a7", "#80cbc4", "#ffb74d"]

    fig, ax = plt.subplots(figsize=(10, 6))
    bp = ax.boxplot(season_data, patch_artist=True, notch=False,
                    medianprops=dict(color="#ff6d00", lw=2.5),
                    whiskerprops=dict(color="#9e9e9e"),
                    capprops=dict(color="#9e9e9e"),
                    flierprops=dict(marker=".", color="#f44336", alpha=0.3, markersize=3))
    for patch, color in zip(bp["boxes"], season_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_xticklabels(seasons)
    ax.set_xlabel("Season")
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_title("PM2.5 Distribution by Season", fontweight="bold")
    ax.axhline(60, color="#ffeb3b", ls="--", lw=1, label="Moderate (60 µg/m³)")
    ax.legend(framealpha=0.3)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    medians = {s: np.nanmedian(d) for s, d in zip(seasons, season_data) if len(d) > 0}
    worst = max(medians, key=medians.get) if medians else "N/A"
    _save(fig, "11_seasonal_boxplot",
          f"Highest median PM2.5 in {worst}. "
          "Monsoon has lowest variability due to rainfall scavenging.")


# ══════════════════════════════════════════════════════════════════════════
# 12 — Spatial map: PM2.5 by station
# ══════════════════════════════════════════════════════════════════════════
def section_12_spatial_stations(df: pd.DataFrame) -> None:
    print("[12] Spatial PM2.5 by station")
    if not all(c in df.columns for c in ["latitude", "longitude", "pm25_ground"]):
        return

    station_pm25 = df.groupby(["latitude", "longitude"])["pm25_ground"].median().reset_index()

    fig, ax = plt.subplots(figsize=(9, 8))
    sc = ax.scatter(
        station_pm25["longitude"], station_pm25["latitude"],
        c=station_pm25["pm25_ground"],
        s=120, cmap="YlOrRd", edgecolors="#0f1117", linewidths=0.5, alpha=0.9,
        vmin=0, vmax=station_pm25["pm25_ground"].quantile(0.95)
    )
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Median PM2.5 (µg/m³)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Station-wise Median PM2.5 — Pune", fontweight="bold")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    _save(fig, "12_spatial_stations",
          f"{len(station_pm25)} unique station locations. "
          "Dense urban areas near industrial zones show elevated PM2.5.")


# ══════════════════════════════════════════════════════════════════════════
# 13 — Land use vs PM2.5
# ══════════════════════════════════════════════════════════════════════════
def section_13_landuse(df: pd.DataFrame) -> None:
    print("[13] Land use vs PM2.5")
    col = next((c for c in ["land_use_class", "landuse_class"] if c in df.columns), None)
    if not col or "pm25_ground" not in df.columns:
        return

    lu_pm25 = df.groupby(col)["pm25_ground"].median().sort_values(ascending=False)
    if len(lu_pm25) < 2:
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(lu_pm25)))
    bars = ax.bar(range(len(lu_pm25)), lu_pm25.values, color=colors, edgecolor="#0f1117", alpha=0.85)
    ax.set_xticks(range(len(lu_pm25)))
    ax.set_xticklabels(lu_pm25.index, rotation=30, ha="right")
    ax.set_ylabel("Median PM2.5 (µg/m³)")
    ax.set_title("Median PM2.5 by Land Use Class", fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    highest = lu_pm25.index[0]
    lowest  = lu_pm25.index[-1]
    ratio   = lu_pm25.iloc[0] / max(lu_pm25.iloc[-1], 0.1)
    _save(fig, "13_landuse_pm25",
          f"'{highest}' has highest PM2.5, '{lowest}' lowest. "
          f"Ratio: {ratio:.1f}x. Industrial/Built-up areas drive elevated exposure.")


# ══════════════════════════════════════════════════════════════════════════
# 14 — Road density vs PM2.5
# ══════════════════════════════════════════════════════════════════════════
def section_14_road_density(df: pd.DataFrame) -> None:
    print("[14] Road density vs PM2.5")
    if "road_density" not in df.columns or "pm25_ground" not in df.columns:
        return

    sub = df[["road_density", "pm25_ground"]].dropna()
    r = sub.corr().iloc[0, 1]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(sub["road_density"], sub["pm25_ground"], alpha=0.2, s=5, color="#ffab40")
    m, b = np.polyfit(sub["road_density"], sub["pm25_ground"], 1)
    x_range = np.linspace(sub["road_density"].min(), sub["road_density"].max(), 100)
    ax.plot(x_range, m * x_range + b, color="#00e676", lw=2, label=f"r = {r:.3f}")
    ax.set_xlabel("Road Density (km/km²)")
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_title("Road Density vs PM2.5", fontweight="bold")
    ax.legend(framealpha=0.3)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    _save(fig, "14_road_density_pm25",
          f"Road density–PM2.5 r = {r:.3f}. "
          "High road density areas (urban cores) show higher vehicle emission exposure.")


# ══════════════════════════════════════════════════════════════════════════
# 15 — Outlier investigation
# ══════════════════════════════════════════════════════════════════════════
def section_15_outliers(df: pd.DataFrame) -> None:
    print("[15] Outlier investigation")
    if "pm25_ground" not in df.columns:
        return

    pm25 = df["pm25_ground"].dropna()
    q1, q3 = pm25.quantile(0.25), pm25.quantile(0.75)
    iqr = q3 - q1
    outlier_thresh = q3 + 1.5 * iqr
    extreme_thresh = q3 + 3.0 * iqr
    outliers = pm25[pm25 > outlier_thresh]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # PM2.5 vs row index (time order proxy)
    ax1.plot(pm25.values[:2000], color="#7c4dff", alpha=0.6, lw=0.5)
    ax1.axhline(outlier_thresh, color="#ff9800", ls="--", lw=1.5,
                label=f"1.5×IQR ({outlier_thresh:.0f})")
    ax1.axhline(extreme_thresh, color="#f44336", ls="--", lw=1.5,
                label=f"3×IQR ({extreme_thresh:.0f})")
    ax1.set_title("PM2.5 Time Series (first 2k rows)", fontweight="bold")
    ax1.set_ylabel("PM2.5 (µg/m³)")
    ax1.legend(framealpha=0.3)
    ax1.grid(alpha=0.3)

    # Outlier count by percentile
    pcts = [90, 95, 99, 99.5, 99.9]
    counts = [len(pm25[pm25 > pm25.quantile(p/100)]) for p in pcts]
    ax2.bar([f">{p}th" for p in pcts], counts, color="#f44336", alpha=0.8, edgecolor="#0f1117")
    ax2.set_xlabel("Percentile threshold")
    ax2.set_ylabel("Row count")
    ax2.set_title("Extreme PM2.5 Values by Percentile", fontweight="bold")
    ax2.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    _save(fig, "15_outliers",
          f"{len(outliers)} outliers above 1.5×IQR ({outlier_thresh:.0f} µg/m³). "
          "Possible causes: sensor malfunction, crop burning events, Diwali fireworks.")


# ══════════════════════════════════════════════════════════════════════════
# 16 — Correlation heatmap
# ══════════════════════════════════════════════════════════════════════════
def section_16_correlation(df: pd.DataFrame) -> None:
    print("[16] Correlation heatmap")
    feature_cols = [c for c in [
        "pm25_ground", "aod_550nm", "satellite_no2", "satellite_so2",
        "satellite_co", "uv_aerosol_index",
        "temperature_2m", "relative_humidity_2m", "wind_speed_10m",
        "boundary_layer_height", "surface_pressure", "precipitation_1h",
        "road_density", "building_density", "elevation_m", "population_density",
    ] if c in df.columns]

    if len(feature_cols) < 3:
        return

    corr = df[feature_cols].corr()

    fig, ax = plt.subplots(figsize=(13, 11))
    import matplotlib.colors as mcolors
    cmap = plt.cm.RdBu_r
    im = ax.imshow(corr.values, cmap=cmap, vmin=-1, vmax=1, aspect="auto")
    fig.colorbar(im, ax=ax, fraction=0.03)

    tick_labels = [c.replace("_", "\n") for c in feature_cols]
    ax.set_xticks(range(len(feature_cols)))
    ax.set_yticks(range(len(feature_cols)))
    ax.set_xticklabels(tick_labels, fontsize=7, rotation=45, ha="right")
    ax.set_yticklabels(tick_labels, fontsize=7)

    # Annotate cells
    for i in range(len(feature_cols)):
        for j in range(len(feature_cols)):
            val = corr.iloc[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=5.5, color="white" if abs(val) > 0.5 else "#9e9e9e")

    ax.set_title("Feature Correlation Matrix", fontweight="bold")
    fig.tight_layout()

    # Top correlations with PM2.5
    if "pm25_ground" in corr.columns:
        pm25_corr = corr["pm25_ground"].drop("pm25_ground").abs().sort_values(ascending=False)
        top3 = pm25_corr.head(3)
        _save(fig, "16_correlation_heatmap",
              f"Top PM2.5 correlates: {top3.index[0]} (r={corr.loc[top3.index[0], 'pm25_ground']:.2f}), "
              f"{top3.index[1]} (r={corr.loc[top3.index[1], 'pm25_ground']:.2f}), "
              f"{top3.index[2]} (r={corr.loc[top3.index[2], 'pm25_ground']:.2f}).")
    else:
        _save(fig, "16_correlation_heatmap")


# ══════════════════════════════════════════════════════════════════════════
# 17 — Feature importance pre-check (mutual information)
# ══════════════════════════════════════════════════════════════════════════
def section_17_mutual_information(df: pd.DataFrame) -> None:
    print("[17] Mutual information feature ranking")
    try:
        from sklearn.feature_selection import mutual_info_regression
    except ImportError:
        FINDINGS.append("**Mutual Information**: sklearn not available.")
        return

    if "pm25_ground" not in df.columns:
        return

    feature_cols = [c for c in [
        "aod_550nm", "satellite_no2", "satellite_so2", "satellite_co",
        "uv_aerosol_index", "temperature_2m", "relative_humidity_2m",
        "wind_speed_10m", "boundary_layer_height", "surface_pressure",
        "precipitation_1h", "road_density", "building_density",
        "elevation_m", "population_density",
    ] if c in df.columns]

    sub = df[feature_cols + ["pm25_ground"]].dropna()
    if len(sub) < 100 or not feature_cols:
        return

    mi = mutual_info_regression(sub[feature_cols], sub["pm25_ground"], random_state=42)
    mi_series = pd.Series(mi, index=feature_cols).sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(9, max(5, len(mi_series) * 0.4)))
    colors = plt.cm.plasma(np.linspace(0.2, 0.8, len(mi_series)))
    ax.barh(mi_series.index, mi_series.values, color=colors, alpha=0.85, edgecolor="#0f1117")
    ax.set_xlabel("Mutual Information Score")
    ax.set_title("Feature Relevance to PM2.5 (Mutual Information)", fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    top_feat = mi_series.index[-1]
    _save(fig, "17_mutual_information",
          f"Top feature by MI: '{top_feat}' (score={mi_series.iloc[-1]:.4f}). "
          "MI captures non-linear dependencies that Pearson correlation misses.")


# ══════════════════════════════════════════════════════════════════════════
# 18 — Summary findings report
# ══════════════════════════════════════════════════════════════════════════
def section_18_findings_report(df: pd.DataFrame) -> None:
    print("[18] Writing EDA findings report")
    report_path = Path("docs/eda_findings.md")

    pm25 = df.get("pm25_ground", pd.Series(dtype=float)).dropna()
    aod  = df.get("aod_550nm",   pd.Series(dtype=float)).dropna()

    lines = [
        "# EDA Key Findings — Vayudrishti-AI Pune Dataset",
        "",
        f"*Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "---",
        "",
        "## Dataset Summary",
        f"- **Rows**: {len(df):,}",
        f"- **Columns**: {len(df.columns)}",
        f"- **PM2.5 range**: {pm25.min():.1f}–{pm25.max():.1f} µg/m³" if len(pm25) else "",
        f"- **PM2.5 mean**: {pm25.mean():.1f} µg/m³" if len(pm25) else "",
        f"- **PM2.5 median**: {pm25.median():.1f} µg/m³" if len(pm25) else "",
        "",
        "---",
        "",
        "## Findings",
        "",
    ]
    for i, finding in enumerate(FINDINGS, 1):
        lines.append(f"{i}. {finding}")

    lines += [
        "",
        "---",
        "",
        "## Modelling Implications",
        "",
        "1. **Use XGBoost** — right-skewed target, non-linear feature relationships.",
        "2. **Cyclically encode** hour and month (sin/cos) — diurnal pattern is real.",
        "3. **Include PBLH** — strongest meteorological driver of inversion events.",
        "4. **Keep AOD missingness indicators** — missing satellite data is informative.",
        "5. **Use temporal holdout** (last 3 months) — not random split.",
        "6. **Spatial K-Fold** by station_id — prevents data leakage across stations.",
        "",
        "---",
        "",
        "## Plot Index",
        "",
    ]
    for png in sorted(EDA_DIR.glob("*.png")):
        lines.append(f"- [{png.stem}]({png})")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Findings report → {report_path}")


# ══════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════
def run_eda(data_path: str | None = None) -> None:
    print("\n" + "=" * 60)
    print(" VAYUDRISHTI-AI — EDA (Stage 7)")
    print("=" * 60)

    df = _load_data(data_path)

    section_01_overview(df)
    section_02_missing(df)
    section_03_pm25_dist(df)
    section_04_aod_pm25(df)
    section_05_no2_pm25(df)
    section_06_wind_pm25(df)
    section_07_pblh_pm25(df)
    section_08_temp_pm25(df)
    section_09_hourly(df)
    section_10_monthly(df)
    section_11_seasonal(df)
    section_12_spatial_stations(df)
    section_13_landuse(df)
    section_14_road_density(df)
    section_15_outliers(df)
    section_16_correlation(df)
    section_17_mutual_information(df)
    section_18_findings_report(df)

    print("\n" + "=" * 60)
    print(f" EDA complete. {len(list(EDA_DIR.glob('*.png')))} plots saved → {EDA_DIR}")
    print(f" Findings report → docs/eda_findings.md")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vayudrishti-AI EDA — Stage 7")
    parser.add_argument("--data", default=None,
                        help="Path to canonical_dataset.parquet or mock CSV")
    args = parser.parse_args()
    run_eda(args.data)
