import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def engineer_features():
    print("Engineering features (rolling means, deltas, seasonal flags)...")
    df = pd.read_csv(config.COMBINED_PROCESSED_FILE, parse_dates=['Date'])
    
    df['Is_Summer'] = df['Date'].dt.month.isin([6, 7, 8]).astype(int)
    df['Month'] = df['Date'].dt.month
    df['Quarter'] = df['Date'].dt.quarter
    
    df['EO_Turbidity_Lag1'] = df['EO_Turbidity'].shift(1)
    df['EO_Turbidity_Lag2'] = df['EO_Turbidity'].shift(2)
    
    df['Rolling_EO_Chl_A_7d'] = df['EO_Chlorophyll_A'].rolling(window=7, min_periods=1).mean()
    df['Rolling_EO_Turbidity_7d'] = df['EO_Turbidity'].rolling(window=7, min_periods=1).mean()
    
    df['Delta_EO_Temp_3d'] = df['EO_Surface_Temp'].diff(periods=3).fillna(0)
    
    nitrate_norm = (df['Nitrate_mgL'] - df['Nitrate_mgL'].min()) / (df['Nitrate_mgL'].max() - df['Nitrate_mgL'].min())
    ammonium_norm = (df['Ammonium_mgL'] - df['Ammonium_mgL'].min()) / (df['Ammonium_mgL'].max() - df['Ammonium_mgL'].min())
    df['Nutrient_Pressure_Index'] = (nitrate_norm + ammonium_norm) / 2
    
    chl_norm = (df['EO_Chlorophyll_A'] - df['EO_Chlorophyll_A'].min()) / (df['EO_Chlorophyll_A'].max() - df['EO_Chlorophyll_A'].min())
    temp_norm = (df['EO_Surface_Temp'] - df['EO_Surface_Temp'].min()) / (df['EO_Surface_Temp'].max() - df['EO_Surface_Temp'].min())
    df['Bloom_Potential_Feature'] = chl_norm * 0.6 + temp_norm * 0.4
    
    df.to_csv(config.FEATURES_FILE, index=False)
    print(f"-> Saved features to {config.FEATURES_FILE}")
    return df

if __name__ == "__main__":
    engineer_features()
