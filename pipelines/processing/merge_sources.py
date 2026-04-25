import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def merge_datasets():
    print("Merging Study and EO Datasets...")
    study_path = os.path.join(config.PROCESSED_DIR, "study_clean.csv")
    eo_path = os.path.join(config.PROCESSED_DIR, "eo_clean.csv")
    
    df_study = pd.read_csv(study_path, parse_dates=['date']) if os.path.exists(study_path) else pd.DataFrame(columns=['date'])
    df_eo = pd.read_csv(eo_path, parse_dates=['date']) if os.path.exists(eo_path) else pd.DataFrame(columns=['date'])
    
    if df_eo.empty and df_study.empty:
        print("ERROR: Both study and EO datasets are empty.")
        return None
        
    df_study = df_study.sort_values('date')
    df_eo = df_eo.sort_values('date')
    df_eo = df_eo.rename(columns={c: f"eo_{c}" for c in df_eo.columns if c not in ['date']})
    
    merged = pd.merge_asof(
        df_eo, df_study, on='date', direction='nearest', tolerance=pd.Timedelta(days=3)
    )
    
    merged['has_insitu'] = ~merged['source'].isna()
    if not merged.empty:
        merged['month'] = merged['date'].dt.month
        merged['season'] = merged['date'].dt.quarter
        merged['day_of_year'] = merged['date'].dt.dayofyear
        
        if 'eo_turbidity_proxy_mean' in merged.columns:
            merged['rolling_7d_turbidity'] = merged['eo_turbidity_proxy_mean'].rolling(window=7, min_periods=1).mean()
            merged['delta_turbidity'] = merged['eo_turbidity_proxy_mean'] - merged['rolling_7d_turbidity']
            
    merged.to_csv(os.path.join(config.PROCESSED_DIR, "merged_dataset.csv"), index=False)
    print(f"Saved merged dataset: {len(merged)} rows, {merged.get('has_insitu', pd.Series()).sum()} overlap rows.")
    return merged

def generate_visuals(df):
    print("Generating visual reports...")
    out_dir = os.path.join(config.PROCESSED_DIR, "visuals")
    os.makedirs(out_dir, exist_ok=True)
    if df is None or df.empty: return
        
    sns.set_theme(style="whitegrid")
    
    plt.figure(figsize=(12, 3))
    plt.scatter(df['date'], [1]*len(df), label="EO Data", alpha=0.5, marker='|', s=100)
    if 'has_insitu' in df.columns:
        study_dates = df[df['has_insitu']]['date']
        plt.scatter(study_dates, [1.1]*len(study_dates), label="Study (In-situ)", color='red', marker='x')
    plt.yticks([])
    plt.title("Data Coverage Timeline")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "data_coverage.png"))
    plt.close()
    
    study_cols = [c for c in df.columns if not c.startswith('eo_') and c not in ['date', 'source', 'location', 'has_insitu', 'month', 'season', 'day_of_year'] and pd.api.types.is_numeric_dtype(df[c])]
    if study_cols:
        plt.figure(figsize=(10, 6))
        df[study_cols].melt().dropna().pipe((sns.boxplot, 'data'), x='value', y='variable')
        plt.title("Study Parameters Distribution")
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "study_parameters_distribution.png"))
        plt.close()
        
    eo_cols = [c for c in df.columns if c.startswith('eo_') and 'mean' in c]
    if eo_cols:
        plt.figure(figsize=(12, 5))
        for c in eo_cols:
            plt.plot(df['date'], df[c], label=c)
        plt.title("EO Indicators Timeseries")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "eo_timeseries_real.png"))
        plt.close()
        
    if 'has_insitu' in df.columns:
        overlap = df[df['has_insitu']]
        if not overlap.empty and len(overlap) > 1:
            corr_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            plt.figure(figsize=(12, 10))
            sns.heatmap(overlap[corr_cols].corr(), annot=False, cmap='coolwarm', center=0)
            plt.title("Correlation Heatmap (Aligned Study + EO)")
            plt.tight_layout()
            plt.savefig(os.path.join(out_dir, "merged_correlation.png"))
            plt.close()

if __name__ == "__main__":
    df = merge_datasets()
    generate_visuals(df)
