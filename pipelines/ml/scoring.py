import pandas as pd
import numpy as np
import os
import sys
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def score_and_predict():
    print("Running scoring and predictions...")
    df = pd.read_csv(config.FEATURES_FILE, parse_dates=['Date'])
    
    df['Bloom_Risk_Score'] = df['Bloom_Potential_Feature'] * 100
    df['Eutrophication_Risk_Score'] = df['Nutrient_Pressure_Index'] * 100
    
    turbidity_penalty = np.minimum((df['EO_Turbidity'] / 10.0) * 30, 40)
    bloom_penalty = df['Bloom_Risk_Score'] * 0.5
    eutro_penalty = df['Eutrophication_Risk_Score'] * 0.3
    
    wqi = 100 - (turbidity_penalty + bloom_penalty + eutro_penalty)
    df['Water_Quality_Score'] = np.clip(wqi, 0, 100)
    
    def assign_alert_level(bloom_risk):
        if bloom_risk > 70:
            return 'Red Alert'
        elif bloom_risk > 40:
            return 'Yellow Alert'
        else:
            return 'Normal'
            
    df['Alert_Level'] = df['Bloom_Risk_Score'].apply(assign_alert_level)
    
    train_mask = df['Is_Study_Actual'] == 1
    features = ['EO_Turbidity', 'EO_Total_Suspended_Matter', 'Month', 'EO_Turbidity_Lag1', 'EO_Turbidity_Lag2']
    
    X_train = df.loc[train_mask, features]
    y_train = df.loc[train_mask, 'Study_Turbidity_NTU']
    
    model = make_pipeline(SimpleImputer(strategy='mean'), RandomForestRegressor(n_estimators=100, random_state=42))
    model.fit(X_train, y_train)
    
    df['Predicted_InSitu_Turbidity'] = model.predict(df[features])
    
    df.to_csv(config.SCORES_FILE, index=False)
    print(f"-> Saved scores and predictions to {config.SCORES_FILE}")
    return df

if __name__ == "__main__":
    score_and_predict()
