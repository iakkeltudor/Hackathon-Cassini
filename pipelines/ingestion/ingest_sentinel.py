import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import rasterio
import rasterio.mask
import geopandas as gpd
from dotenv import load_dotenv
import glob
import numpy as np
from tqdm import tqdm
import zipfile
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

load_dotenv()

def download_sentinel_data(user, password, download_dir):
    try:
        # We use direct STAC API for CDSE
        import geopandas as gpd
        import json
        
        from shapely.geometry import mapping
        
        boundary_path = os.path.join(config.STORAGE_DIR, "layers", "tarnita_lake_boundary.geojson")
        if not os.path.exists(boundary_path):
            print(f"Cannot download: Boundary file not found at {boundary_path}")
            return
            
        gdf = gpd.read_file(boundary_path)
        if gdf.crs is None or gdf.crs.to_string() != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
        wkt = gdf.geometry.union_all().wkt
        
        # Hardcoding summer 2023 to ensure we find real data matching the 'Sinteza 2023' report
        start_date = "2023-06-01T00:00:00.000Z"
        end_date = "2023-08-30T00:00:00.000Z"
        
        print(f"Querying Copernicus CDSE OData API for Sentinel-2 L2A images in Summer 2023...")
        
        query_url = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq 'SENTINEL-2' and OData.CSC.Intersects(area=geography'SRID=4326;{wkt}') and ContentDate/Start ge {start_date} and ContentDate/Start le {end_date} and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq 'S2MSI2A')&$top=20&$expand=Attributes"
        
        resp = requests.get(query_url)
        resp.raise_for_status()
        products = resp.json().get("value", [])
        
        if not products:
            print("No products found for the given criteria.")
            return
            
        def get_cloud_cover(prod):
            for attr in prod.get("Attributes", []):
                if attr.get("Name") == "cloudCover":
                    return attr.get("Value", 100)
            return 100
            
        products.sort(key=get_cloud_cover)
        best_product = products[0]
        best_product_id = best_product["Id"]
        product_title = best_product["Name"]
        
        print(f"Found {len(products)} products. Attempting to download the clearest one ({get_cloud_cover(best_product)}% clouds): {product_title}")
        
        # --- CDSE Custom Download via Keycloak Token ---
        print("Authenticating with CDSE Keycloak for download token...")
        token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        token_data = {
            "client_id": "cdse-public",
            "username": user,
            "password": password,
            "grant_type": "password",
        }
        token_resp = requests.post(token_url, data=token_data)
        
        if token_resp.status_code != 200:
            print(f"Failed to get token: {token_resp.text}")
            return
            
        access_token = token_resp.json().get("access_token")
        
        download_url_value = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products({best_product_id})/$value"
        zip_path = os.path.join(download_dir, f"{product_title}.zip")
        
        print(f"Downloading (This may take a few minutes as satellite imagery is large)...")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        with requests.get(download_url_value, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
                    
        print("Download successful! Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(download_dir)
        os.remove(zip_path)
        print("Extraction complete.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Download failed: {e}")

def calculate_indices(bands_dict):
    eps = 1e-8
    b3 = bands_dict.get('B03')
    b4 = bands_dict.get('B04')
    b5 = bands_dict.get('B05')
    
    results = {}
    if b4 is not None and b5 is not None:
        results['ndci'] = (b5 - b4) / (b5 + b4 + eps)
        results['chl_proxy'] = (b5 / (b4 + eps)) * 10.5
        
    if b3 is not None and b4 is not None:
        results['turbidity_proxy'] = (b4 / (b3 + eps)) * 15.0
        results['tsm_proxy'] = (b4 * 2.5) + 5.0
        
    return results

def get_lake_geometry():
    boundary_path = os.path.join(config.STORAGE_DIR, "layers", "tarnita_lake_boundary.geojson")
    if not os.path.exists(boundary_path):
        return None
    gdf = gpd.read_file(boundary_path)
    return gdf.geometry.values

def ingest_sentinel_data():
    print("Starting Sentinel-2 Real Data Ingestion...")
    user = os.environ.get("CDSE_USER")
    password = os.environ.get("CDSE_PASSWORD")
    
    sentinel_raw_dir = os.path.join(config.RAW_DIR, "sentinel")
    os.makedirs(sentinel_raw_dir, exist_ok=True)
    
    if not user or not password:
        print("WARNING: CDSE_USER or CDSE_PASSWORD not set. Skipping actual download.")
    else:
        print("Authentication configured. Attempting CDSE API download...")
        download_sentinel_data(user, password, sentinel_raw_dir)
    
    safe_dirs = glob.glob(os.path.join(sentinel_raw_dir, "*.SAFE"))
    if not safe_dirs:
        print(f"No Sentinel-2 .SAFE directories found in {sentinel_raw_dir}.")
        df = pd.DataFrame(columns=['date', 'cloud_cover', 'ndci_mean', 'chl_proxy_mean', 'turbidity_proxy_mean', 'tsm_mean', 'source'])
        df.to_csv(os.path.join(config.PROCESSED_DIR, "eo_clean.csv"), index=False)
        return
        
    lake_geoms = get_lake_geometry()
    timeseries = []
    
    for safe_dir in tqdm(safe_dirs, desc="Processing Sentinel-2 Images"):
        try:
            date_str = os.path.basename(safe_dir).split('_')[2][:8]
            date_obj = datetime.strptime(date_str, "%Y%m%d")
        except: continue
            
        bands_paths = {
            'B03': glob.glob(os.path.join(safe_dir, "GRANULE", "*", "IMG_DATA", "R10m", "*_B03_10m.jp2")),
            'B04': glob.glob(os.path.join(safe_dir, "GRANULE", "*", "IMG_DATA", "R10m", "*_B04_10m.jp2")),
            'B05': glob.glob(os.path.join(safe_dir, "GRANULE", "*", "IMG_DATA", "R20m", "*_B05_20m.jp2")),
        }
        
        bands_data = {}
        for band, paths in bands_paths.items():
            if not paths: continue
            with rasterio.open(paths[0]) as src:
                if lake_geoms is not None:
                    try:
                        out_image, out_transform = rasterio.mask.mask(src, lake_geoms, crop=True)
                        valid_pixels = out_image[0][out_image[0] > 0]
                        bands_data[band] = valid_pixels.astype(float) / 10000.0
                    except ValueError: pass
        
        if 'B04' in bands_data:
            indices = calculate_indices(bands_data)
            row = {'date': date_obj, 'cloud_cover': 0, 'source': 'sentinel2'}
            if 'ndci' in indices and len(indices['ndci']) > 0:
                row['ndci_mean'] = np.mean(indices['ndci'])
                row['chl_proxy_mean'] = np.mean(indices['chl_proxy'])
            if 'turbidity_proxy' in indices and len(indices['turbidity_proxy']) > 0:
                row['turbidity_proxy_mean'] = np.mean(indices['turbidity_proxy'])
                row['tsm_mean'] = np.mean(indices['tsm_proxy'])
            timeseries.append(row)
            
    df = pd.DataFrame(timeseries)
    if not df.empty: df = df.sort_values('date')
    df.to_csv(os.path.join(config.PROCESSED_DIR, "eo_clean.csv"), index=False)

if __name__ == "__main__":
    ingest_sentinel_data()
