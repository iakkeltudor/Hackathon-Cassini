import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def align_and_combine_datasets():
    print("Aligning temporal data and building combined dataset...")
    os.makedirs(config.PROCESSED_DIR, exist_ok=True)
    
    df_study = pd.read_csv(config.STUDY_RAW_FILE, parse_dates=['Date'])
    df_eo = pd.read_csv(config.EO_RAW_FILE, parse_dates=['Date'])
    
    df_study.set_index('Date', inplace=True)
    df_eo.set_index('Date', inplace=True)
    
    full_index = pd.date_range(start=min(df_study.index.min(), df_eo.index.min()), 
                               end=max(df_study.index.max(), df_eo.index.max()), freq='D')
                               
    df_study = df_study.reindex(full_index)
    df_eo = df_eo.reindex(full_index)
    
    df_study_filled = df_study.interpolate(method='linear', limit=7).ffill()
    df_eo_filled = df_eo.interpolate(method='linear', limit=5).ffill()
    
    combined_df = pd.concat([df_study_filled, df_eo_filled], axis=1)
    combined_df.index.name = 'Date'
    
    combined_df['Is_Study_Actual'] = combined_df.index.isin(pd.read_csv(config.STUDY_RAW_FILE, parse_dates=['Date'])['Date']).astype(int)
    combined_df['Is_EO_Actual'] = combined_df.index.isin(pd.read_csv(config.EO_RAW_FILE, parse_dates=['Date'])['Date']).astype(int)
    
    combined_df.reset_index(inplace=True)
    combined_df.to_csv(config.COMBINED_PROCESSED_FILE, index=False)
    print(f"-> Saved combined dataset to {config.COMBINED_PROCESSED_FILE}")
    
    return combined_df

if __name__ == "__main__":
    align_and_combine_datasets()
