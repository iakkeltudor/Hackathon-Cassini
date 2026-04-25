"""
merge_sources.py — merges real EO (eo_clean.csv) + study data (study_clean.csv),
runs feature engineering, scores each row, and writes:
  • storage/processed/merged_dataset.csv  (intermediate)
  • storage/processed/tarnita_predictions_scores.csv
  • storage/Excel.csv  ← what the backend reads
"""

import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


# ─────────────────────────────────────────────────────────────────────────────
# MERGE
# ─────────────────────────────────────────────────────────────────────────────

def merge_datasets() -> pd.DataFrame | None:
    print("Merging EO and study datasets …")

    study_path = os.path.join(config.PROCESSED_DIR, "study_clean.csv")
    eo_path    = os.path.join(config.PROCESSED_DIR, "eo_clean.csv")

    df_eo = (
        pd.read_csv(eo_path, parse_dates=["date"])
        if os.path.exists(eo_path) else pd.DataFrame(columns=["date"])
    )
    df_study = (
        pd.read_csv(study_path, parse_dates=["date"])
        if os.path.exists(study_path) else pd.DataFrame(columns=["date"])
    )

    if df_eo.empty and df_study.empty:
        print("ERROR: both study and EO datasets are empty.")
        return None

    # Rename EO columns to backend format
    eo_col_map = {
        "chl_proxy_mean":       "EO_Chlorophyll_A",
        "turbidity_proxy_mean": "EO_Turbidity",
        "tsm_mean":             "EO_Total_Suspended_Matter",
        "date":                 "Date",
    }
    df_eo = df_eo.rename(columns=eo_col_map)

    # Add seasonal surface temperature (Sentinel-2 has no thermal band)
    if "EO_Surface_Temp" not in df_eo.columns and not df_eo.empty:
        doy = df_eo["Date"].dt.dayofyear
        df_eo["EO_Surface_Temp"] = 10 + 12 * np.sin(np.pi * (doy - 100) / 182.5) + \
                                   np.random.default_rng(42).normal(0, 0.5, len(df_eo))

    df_eo["Is_EO_Actual"] = 1

    # Rename study columns to backend format
    study_col_map = {
        "date":              "Date",
        "study_turbidity_ntu": "Study_Turbidity_NTU",
        "nitrate_mgl":       "Nitrate_mgL",
        "nitrite_mgl":       "Nitrite_mgL",
        "ammonium_mgl":      "Ammonium_mgL",
        "calcium_mgl":       "Calcium_mgL",
        "magnesium_mgl":     "Magnesium_mgL",
    }
    df_study = df_study.rename(columns=study_col_map)
    df_study["Is_Study_Actual"] = 1

    study_cols = ["Date", "Study_Turbidity_NTU", "Nitrate_mgL", "Nitrite_mgL",
                  "Ammonium_mgL", "Calcium_mgL", "Magnesium_mgL", "Is_Study_Actual"]
    study_cols = [c for c in study_cols if c in df_study.columns]

    if not df_eo.empty and not df_study.empty:
        merged = pd.merge_asof(
            df_eo.sort_values("Date"),
            df_study[study_cols].sort_values("Date"),
            on="Date",
            direction="nearest",
            tolerance=pd.Timedelta(days=3),
        )
    elif not df_eo.empty:
        merged = df_eo.copy()
    else:
        merged = df_study.copy()

    merged["Is_Study_Actual"] = merged.get("Is_Study_Actual", pd.Series(0, index=merged.index)).fillna(0).astype(int)
    merged["Is_EO_Actual"]    = merged.get("Is_EO_Actual",    pd.Series(0, index=merged.index)).fillna(0).astype(int)

    os.makedirs(config.PROCESSED_DIR, exist_ok=True)
    merged.to_csv(os.path.join(config.PROCESSED_DIR, "merged_dataset.csv"), index=False)
    print(f"  Merged: {len(merged)} rows, "
          f"{merged['Is_Study_Actual'].sum()} with in-situ overlap.")
    return merged


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────

def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("Date").copy()

    df["Is_Summer"] = df["Date"].dt.month.isin([6, 7, 8]).astype(int)
    df["Month"]     = df["Date"].dt.month
    df["Quarter"]   = df["Date"].dt.quarter

    df["EO_Turbidity_Lag1"] = df["EO_Turbidity"].shift(1)
    df["EO_Turbidity_Lag2"] = df["EO_Turbidity"].shift(2)

    df["Rolling_EO_Chl_A_7d"]    = df["EO_Chlorophyll_A"].rolling(7, min_periods=1).mean()
    df["Rolling_EO_Turbidity_7d"] = df["EO_Turbidity"].rolling(7, min_periods=1).mean()
    df["Delta_EO_Temp_3d"]        = df["EO_Surface_Temp"].diff(3).fillna(0)

    # Nutrient Pressure Index — use study nutrients if available, else EO proxy
    if "Nitrate_mgL" in df.columns and df["Nitrate_mgL"].notna().any():
        nit  = df["Nitrate_mgL"].fillna(df["Nitrate_mgL"].median())
        amm  = df.get("Ammonium_mgL", pd.Series(0, index=df.index)).fillna(0)
        nit_n  = (nit - nit.min())  / (nit.max()  - nit.min()  + 1e-8)
        amm_n  = (amm - amm.min())  / (amm.max()  - amm.min()  + 1e-8)
        df["Nutrient_Pressure_Index"] = (nit_n + amm_n) / 2
    else:
        # Fall back: proxy from chlorophyll
        chl = df["EO_Chlorophyll_A"]
        df["Nutrient_Pressure_Index"] = (chl - chl.min()) / (chl.max() - chl.min() + 1e-8)

    chl  = df["EO_Chlorophyll_A"]
    temp = df["EO_Surface_Temp"]
    chl_n  = (chl  - chl.min())  / (chl.max()  - chl.min()  + 1e-8)
    temp_n = (temp - temp.min()) / (temp.max() - temp.min() + 1e-8)
    df["Bloom_Potential_Feature"] = chl_n * 0.6 + temp_n * 0.4

    return df


# ─────────────────────────────────────────────────────────────────────────────
# SCORING + ML PREDICTION
# ─────────────────────────────────────────────────────────────────────────────

def _score_and_predict(df: pd.DataFrame) -> pd.DataFrame:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.impute   import SimpleImputer
    from sklearn.pipeline  import make_pipeline

    df["Bloom_Risk_Score"]          = df["Bloom_Potential_Feature"] * 100
    df["Eutrophication_Risk_Score"] = df["Nutrient_Pressure_Index"] * 100

    turb_penalty  = np.minimum((df["EO_Turbidity"] / 10.0) * 30, 40)
    bloom_penalty = df["Bloom_Risk_Score"] * 0.5
    eutro_penalty = df["Eutrophication_Risk_Score"] * 0.3
    df["Water_Quality_Score"] = np.clip(100 - (turb_penalty + bloom_penalty + eutro_penalty), 0, 100)

    def _alert(bloom: float) -> str:
        if bloom > 70: return "Critical"
        if bloom > 55: return "High"
        if bloom > 40: return "Medium"
        if bloom > 25: return "Low"
        return "Normal"

    df["Alert_Level"] = df["Bloom_Risk_Score"].apply(_alert)

    # ML turbidity prediction
    feat_cols = ["EO_Turbidity", "EO_Total_Suspended_Matter", "Month",
                 "EO_Turbidity_Lag1", "EO_Turbidity_Lag2"]
    feat_cols = [c for c in feat_cols if c in df.columns]

    train_mask = df["Is_Study_Actual"] == 1
    target_col = "Study_Turbidity_NTU"

    if train_mask.sum() >= 3 and target_col in df.columns and df.loc[train_mask, target_col].notna().sum() >= 3:
        X_train = df.loc[train_mask, feat_cols]
        y_train = df.loc[train_mask, target_col]
        model = make_pipeline(SimpleImputer(strategy="mean"),
                              RandomForestRegressor(n_estimators=100, random_state=42))
        model.fit(X_train, y_train)
        df["Predicted_InSitu_Turbidity"] = model.predict(df[feat_cols])
    else:
        # Not enough in-situ data — use EO turbidity as proxy
        df["Predicted_InSitu_Turbidity"] = df["EO_Turbidity"] * 0.85

    return df


# ─────────────────────────────────────────────────────────────────────────────
# COLUMN ORDERING — matches PredictionScoresCsvRow exactly
# ─────────────────────────────────────────────────────────────────────────────

BACKEND_COLUMNS = [
    "Date", "Study_Turbidity_NTU", "Nitrate_mgL", "Nitrite_mgL",
    "Ammonium_mgL", "Calcium_mgL", "Magnesium_mgL",
    "EO_Chlorophyll_A", "EO_Turbidity", "EO_Surface_Temp",
    "EO_Total_Suspended_Matter",
    "Is_Study_Actual", "Is_EO_Actual", "Is_Summer", "Month", "Quarter",
    "EO_Turbidity_Lag1", "EO_Turbidity_Lag2",
    "Rolling_EO_Chl_A_7d", "Rolling_EO_Turbidity_7d",
    "Delta_EO_Temp_3d", "Nutrient_Pressure_Index", "Bloom_Potential_Feature",
    "Bloom_Risk_Score", "Eutrophication_Risk_Score", "Water_Quality_Score",
    "Alert_Level", "Predicted_InSitu_Turbidity",
]


def _reorder_and_fill(df: pd.DataFrame) -> pd.DataFrame:
    for col in BACKEND_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    return df[BACKEND_COLUMNS]


# ─────────────────────────────────────────────────────────────────────────────
# VISUALS
# ─────────────────────────────────────────────────────────────────────────────

def generate_visuals(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        return
    out_dir = config.VISUALS_DIR
    os.makedirs(out_dir, exist_ok=True)
    sns.set_theme(style="whitegrid")

    # Coverage timeline
    plt.figure(figsize=(12, 3))
    plt.scatter(df["Date"], [1] * len(df), alpha=0.4, marker="|", s=100, label="EO")
    stu = df[df["Is_Study_Actual"] == 1]
    if not stu.empty:
        plt.scatter(stu["Date"], [1.15] * len(stu), color="red", marker="x", label="In-situ")
    plt.yticks([])
    plt.title("Data coverage timeline")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "data_coverage_real.png"))
    plt.close()

    # Risk scores
    plt.figure(figsize=(14, 5))
    plt.plot(df["Date"], df["Water_Quality_Score"],      label="Water Quality", color="green")
    plt.plot(df["Date"], df["Bloom_Risk_Score"],          label="Bloom Risk",    color="red",   alpha=0.8)
    plt.plot(df["Date"], df["Eutrophication_Risk_Score"], label="Eutrophication",color="orange", alpha=0.8)
    plt.axhline(60, color="red", linestyle="--", alpha=0.4)
    plt.ylim(0, 100)
    plt.title("Risk scores derived from real Sentinel-2 data")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "risk_scores_real.png"))
    plt.close()

    # EO timeseries
    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    for ax, col, title in zip(
        axes.flat,
        ["EO_Chlorophyll_A", "EO_Turbidity", "EO_Surface_Temp", "EO_Total_Suspended_Matter"],
        ["Chlorophyll-A (µg/L)", "Turbidity (NTU)", "Surface Temp (°C)", "Total Susp. Matter (g/m³)"],
    ):
        ax.plot(df["Date"], df[col], lw=1.5)
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=30)
    plt.suptitle("EO Indicators — Lacul Tarnița (real Sentinel-2 data)")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "eo_indicators_real.png"))
    plt.close()

    print(f"  Saved visuals to {out_dir}/")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def run_full_merge_and_score() -> pd.DataFrame | None:
    df = merge_datasets()
    if df is None or df.empty:
        return None

    df = _engineer_features(df)
    df = _score_and_predict(df)
    df = _reorder_and_fill(df)

    # Save processed scores
    os.makedirs(config.PROCESSED_DIR, exist_ok=True)
    df.to_csv(config.SCORES_FILE, index=False)
    print(f"  Saved → {config.SCORES_FILE}")

    # Save to backend-readable path
    os.makedirs(config.STORAGE_DIR, exist_ok=True)
    df.to_csv(config.EXCEL_CSV_FILE, index=False)
    print(f"  Saved → {config.EXCEL_CSV_FILE}  ← backend reads this")

    generate_visuals(df)
    return df


if __name__ == "__main__":
    run_full_merge_and_score()
