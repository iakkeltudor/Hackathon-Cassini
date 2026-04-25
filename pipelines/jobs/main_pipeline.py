import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.mock_data_generator import generate_mock_data
from processing.process import align_and_combine_datasets
from processing.feature_engineering import engineer_features
from ml.scoring import score_and_predict
from ml.visualize import generate_visuals

def run():
    print("="*50)
    print(" WATER QUALITY PIPELINE - TARNITA MVP")
    print("="*50)
    
    generate_mock_data()
    align_and_combine_datasets()
    engineer_features()
    score_and_predict()
    generate_visuals()
    
    print("="*50)
    print(" PIPELINE FINISHED SUCCESSFULLY")
    print(" Check storage/processed/visuals for charts.")
    print(" Check storage/processed for final datasets.")
    print("="*50)

if __name__ == "__main__":
    run()
