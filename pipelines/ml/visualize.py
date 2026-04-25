import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def generate_visuals():
    print("Generating visual outputs...")
    os.makedirs(config.VISUALS_DIR, exist_ok=True)
    df = pd.read_csv(config.SCORES_FILE, parse_dates=['Date'])
    
    sns.set_theme(style="whitegrid")
    
    plt.figure(figsize=(12, 5))
    plt.plot(df['Date'], df['EO_Chlorophyll_A'], label='EO Chl-a', color='green')
    plt.plot(df['Date'], df['EO_Turbidity'], label='EO Turbidity', color='orange')
    plt.plot(df['Date'], df['EO_Total_Suspended_Matter'], label='EO TSM', color='brown')
    plt.title('Satellite (EO) Indicators Over Time')
    plt.ylabel('Value')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(config.VISUALS_DIR, '01_eo_timeseries.png'))
    plt.close()
    
    plt.figure(figsize=(12, 5))
    plt.plot(df['Date'], df['EO_Turbidity'], label='Satellite Proxy Turbidity', alpha=0.6)
    actuals = df[df['Is_Study_Actual'] == 1]
    plt.scatter(actuals['Date'], actuals['Study_Turbidity_NTU'], color='red', label='In-situ Study Turbidity', zorder=5)
    plt.title('Satellite Proxy vs In-Situ Study Measurements')
    plt.ylabel('Turbidity (NTU)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(config.VISUALS_DIR, '02_study_vs_eo.png'))
    plt.close()
    
    plt.figure(figsize=(12, 5))
    plt.plot(df['Date'], df['Water_Quality_Score'], label='Water Quality Index', color='blue')
    plt.plot(df['Date'], df['Bloom_Risk_Score'], label='Bloom Risk Score', color='red', linestyle='-')
    plt.axhline(y=70, color='darkred', linestyle='--', label='Red Alert Threshold (>70)')
    plt.axhline(y=40, color='orange', linestyle='--', label='Yellow Alert Threshold (>40)')
    plt.fill_between(df['Date'], 70, 100, color='red', alpha=0.1)
    plt.fill_between(df['Date'], 40, 70, color='orange', alpha=0.1)
    plt.title('Risk Scores Evolution & Alert Thresholds')
    plt.ylabel('Score (0-100)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(config.VISUALS_DIR, '03_risk_scores.png'))
    plt.close()
    
    plt.figure(figsize=(12, 10))
    cols = ['Study_Turbidity_NTU', 'EO_Chlorophyll_A', 'EO_Turbidity', 'EO_Turbidity_Lag1', 'Month', 'Water_Quality_Score']
    corr = df[cols].corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
    plt.title('Correlation between Variables (Including Lags & Seasonality)')
    plt.tight_layout()
    plt.savefig(os.path.join(config.VISUALS_DIR, '04_correlation_heatmap.png'))
    plt.close()
    
    plt.figure(figsize=(8, 8))
    actuals = df[df['Is_Study_Actual'] == 1]
    plt.scatter(actuals['Study_Turbidity_NTU'], actuals['Predicted_InSitu_Turbidity'], alpha=0.7)
    plt.plot([actuals['Study_Turbidity_NTU'].min(), actuals['Study_Turbidity_NTU'].max()],
             [actuals['Study_Turbidity_NTU'].min(), actuals['Study_Turbidity_NTU'].max()], 'r--')
    plt.xlabel('Actual In-situ Turbidity (NTU)')
    plt.ylabel('Predicted Turbidity (NTU)')
    plt.title('Prediction Sanity Check (Random Forest with Time Lags & Seasonality)')
    plt.tight_layout()
    plt.savefig(os.path.join(config.VISUALS_DIR, '05_prediction_scatter.png'))
    plt.close()
    
    print(f"-> Generated 5 visual reports in {config.VISUALS_DIR}")

if __name__ == "__main__":
    generate_visuals()
