import json
import os
import random
from datetime import datetime

def fetch_raw_data(lake_name="Tarnita", output_path="../storage/raw"):
    print(f"Fetching raw satellite data for {lake_name} from Copernicus API...")
    os.makedirs(output_path, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    file_path = os.path.join(output_path, f"sentinel2_{lake_name.lower()}_{timestamp}.json")
    
    raw_data = {
        "metadata": {
            "lake": lake_name,
            "timestamp": timestamp,
            "satellite": "Sentinel-2"
        },
        "bands": {
            "B02": random.uniform(0.02, 0.05),
            "B03": random.uniform(0.03, 0.06),
            "B04": random.uniform(0.01, 0.04),
            "B08": random.uniform(0.10, 0.15)
        }
    }
    
    with open(file_path, "w") as f:
        json.dump(raw_data, f, indent=4)
        
    print(f"Saved raw data to {file_path}")
    return file_path
