import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def generate_mock_data():
    print("Generating mock study and satellite data...")
    os.makedirs(config.RAW_DIR, exist_ok=True)
    
    dates = pd.date_range(start="2026-01-01", end="2026-12-31", freq='D')
    
    study_dates = dates[::7]
    np.random.seed(42)
    
    study_data = pd.DataFrame({
        'Date': study_dates,
        'Study_Turbidity_NTU': np.random.normal(loc=3.5, scale=1.2, size=len(study_dates)).clip(0.1),
        'Nitrate_mgL': np.random.normal(loc=1.2, scale=0.4, size=len(study_dates)).clip(0),
        'Nitrite_mgL': np.random.normal(loc=0.05, scale=0.02, size=len(study_dates)).clip(0),
        'Ammonium_mgL': np.random.normal(loc=0.1, scale=0.05, size=len(study_dates)).clip(0),
        'Calcium_mgL': np.random.normal(loc=45.0, scale=5.0, size=len(study_dates)).clip(10),
        'Magnesium_mgL': np.random.normal(loc=12.0, scale=2.0, size=len(study_dates)).clip(1)
    })
    
    summer_mask = (study_data['Date'].dt.month >= 6) & (study_data['Date'].dt.month <= 8)
    study_data.loc[summer_mask, 'Study_Turbidity_NTU'] += np.random.normal(2.0, 0.5, size=summer_mask.sum())
    study_data.loc[summer_mask, 'Nitrate_mgL'] += np.random.normal(0.8, 0.2, size=summer_mask.sum())
    
    study_data.to_csv(config.STUDY_RAW_FILE, index=False)
    print(f"-> Saved mock study data to {config.STUDY_RAW_FILE}")
    
    eo_dates = dates[::5]
    
    eo_data = pd.DataFrame({
        'Date': eo_dates,
        'EO_Chlorophyll_A': np.random.normal(loc=2.0, scale=0.5, size=len(eo_dates)).clip(0),
        'EO_Turbidity': np.random.normal(loc=3.8, scale=1.5, size=len(eo_dates)).clip(0.1),
        'EO_Surface_Temp': 10 + 12 * np.sin(np.pi * (eo_dates.dayofyear - 100) / 182.5) + np.random.normal(0, 1, size=len(eo_dates)),
        'EO_Total_Suspended_Matter': np.random.normal(loc=10.0, scale=3.0, size=len(eo_dates)).clip(1.0)
    })
    
    eo_summer = (eo_data['Date'].dt.month >= 6) & (eo_data['Date'].dt.month <= 8)
    eo_data.loc[eo_summer, 'EO_Chlorophyll_A'] += np.random.normal(3.0, 1.0, size=eo_summer.sum())
    eo_data.loc[eo_summer, 'EO_Turbidity'] += np.random.normal(1.5, 0.5, size=eo_summer.sum())
    
    eo_data.to_csv(config.EO_RAW_FILE, index=False)
    print(f"-> Saved mock EO data to {config.EO_RAW_FILE}")

if __name__ == "__main__":
    generate_mock_data()
