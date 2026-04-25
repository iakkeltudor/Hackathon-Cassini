import json
import os

def compute_indicators(raw_file_path, output_path="../storage/processed"):
    print(f"Processing {raw_file_path} to compute water indicators...")
    os.makedirs(output_path, exist_ok=True)
    
    with open(raw_file_path, "r") as f:
        raw_data = json.load(f)
        
    bands = raw_data["bands"]
    ndwi = (bands["B03"] - bands["B08"]) / (bands["B03"] + bands["B08"] + 0.0001)
    chla_proxy = (bands["B04"] / (bands["B08"] + 0.0001)) * 10.5
    turbidity = bands["B04"] * 100
    
    processed_data = {
        "metadata": raw_data["metadata"],
        "indicators": {
            "chlorophyll_a": chla_proxy,
            "turbidity": turbidity,
            "total_suspended_matter": turbidity * 1.5,
            "surface_temperature": 20.5 + ndwi
        }
    }
    
    file_name = os.path.basename(raw_file_path).replace("raw", "processed")
    out_file = os.path.join(output_path, file_name)
    
    with open(out_file, "w") as f:
        json.dump(processed_data, f, indent=4)
        
    print(f"Saved processed indicators to {out_file}")
    return out_file
