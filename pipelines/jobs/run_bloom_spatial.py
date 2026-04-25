import os
import sys
from datetime import datetime
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processing import bloom_spatial
from rasterio.transform import from_origin

def run():
    print("="*50)
    print(" STARTING SPATIAL BLOOM DETECTION (MOCK SENTINEL-2 L2A)")
    print("="*50)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    storage_processed = os.path.join(base_dir, "storage", "processed")
    storage_layers = os.path.join(base_dir, "storage", "layers")
    visuals_dir = os.path.join(storage_processed, "visuals")
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    boundary_path = os.path.join(storage_layers, "tarnita_lake_boundary.geojson")
    if not os.path.exists(boundary_path):
        bloom_spatial.generate_mock_lake_boundary(boundary_path)
        print(f"[OK] Generated mock boundary at {boundary_path}")
        
    width, height = 200, 100
    b3, b4, b5, b8a = bloom_spatial.create_mock_sentinel_bands(width, height)
    print(f"[OK] Generated mock Sentinel-2 arrays (simulated bloom in NW)")
    
    transform = from_origin(23.27, 46.73, 0.00025, 0.0002)
    mask = bloom_spatial.mask_to_lake((height, width))
    
    ndci = bloom_spatial.calculate_ndci(b5, b4)
    chl = bloom_spatial.calculate_chl_proxy(b4, b8a)
    print("[OK] Calculated NDCI and Chlorophyll proxies")
    
    classified = bloom_spatial.classify_bloom_risk(ndci)
    
    ndci_path = os.path.join(storage_processed, f"ndci_{date_str}.tif")
    class_path = os.path.join(storage_processed, f"bloom_classified_{date_str}.tif")
    bloom_spatial.save_raster(ndci.astype('float32'), ndci_path, transform)
    bloom_spatial.save_raster(classified, class_path, transform)
    print(f"[OK] Exported NDCI and Risk rasters to {storage_processed}")
    
    zones = bloom_spatial.raster_to_vector_zones(classified, transform, mask)
    geojson_path = os.path.join(storage_processed, f"bloom_zones_{date_str}.geojson")
    bloom_spatial.export_geojson(zones, geojson_path, date_str)
    print(f"[OK] Vectorized bloom zones to {geojson_path}")
    
    bloom_spatial.generate_all_visuals(ndci, classified, chl, mask, transform, date_str, visuals_dir)
    print(f"[OK] Generated 5 required visuals in {visuals_dir}")
    
    print("\n--- SUMMARY ---")
    print(f"Date Processed: {date_str}")
    total_lake_pixels = np.sum(mask)
    for cls_val, cls_name in zip([1,2,3,4], ['No Bloom', 'Low Risk', 'Medium Risk', 'High Risk']):
        count = np.sum((classified == cls_val) & mask)
        pct = (count / total_lake_pixels) * 100
        print(f" - {cls_name}: {pct:.1f}%")
        
    print("="*50)

if __name__ == "__main__":
    run()
