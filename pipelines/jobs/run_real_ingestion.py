import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingestion import ingest_study, ingest_sentinel
from processing import merge_sources
import config

def run(study_path):
    print("="*50)
    print(" STARTING REAL DATA INGESTION PIPELINE")
    print("="*50)
    
    print(f"1. Processing Study File: {study_path}")
    ingest_study.process_study_file(study_path)
    
    print("\n2. Processing Sentinel-2 Data")
    ingest_sentinel.ingest_sentinel_data()
    
    print("\n3. Merging Sources and Engineering Features")
    df = merge_sources.merge_datasets()
    
    print("\n4. Generating Visualizations")
    merge_sources.generate_visuals(df)
    
    print("="*50)
    print(" PIPELINE COMPLETED")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", type=str, required=True, help="Path to study file (CSV or PDF)")
    args = parser.parse_args()
    
    run(args.study)
