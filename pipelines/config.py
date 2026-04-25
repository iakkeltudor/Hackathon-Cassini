import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")

RAW_DIR = os.path.join(STORAGE_DIR, "raw")
PROCESSED_DIR = os.path.join(STORAGE_DIR, "processed")
VISUALS_DIR = os.path.join(PROCESSED_DIR, "visuals")

STUDY_RAW_FILE = os.path.join(RAW_DIR, "tarnita_study_data.csv")
EO_RAW_FILE = os.path.join(RAW_DIR, "tarnita_eo_data.csv")
COMBINED_PROCESSED_FILE = os.path.join(PROCESSED_DIR, "tarnita_combined_dataset.csv")
FEATURES_FILE = os.path.join(PROCESSED_DIR, "tarnita_features.csv")
SCORES_FILE = os.path.join(PROCESSED_DIR, "tarnita_predictions_scores.csv")
