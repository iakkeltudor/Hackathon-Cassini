import os
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape, Polygon
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches
import json

NDCI_THRESHOLDS = {
    "no_bloom": 0.0,
    "low": 0.2,
    "medium": 0.4
}

def generate_mock_lake_boundary(out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    polygon = Polygon([
        [23.27, 46.73],
        [23.32, 46.73],
        [23.32, 46.71],
        [23.27, 46.71],
        [23.27, 46.73]
    ])
    gdf = gpd.GeoDataFrame([1], geometry=[polygon], crs="EPSG:4326")
    gdf.to_file(out_path, driver="GeoJSON")
    return out_path

def create_mock_sentinel_bands(width=200, height=100):
    b3 = np.random.normal(0.04, 0.01, (height, width))
    b4 = np.random.normal(0.03, 0.01, (height, width))
    b5 = np.random.normal(0.03, 0.01, (height, width))
    b8a = np.random.normal(0.02, 0.01, (height, width))

    y, x = np.ogrid[:height, :width]
    center_x, center_y = width * 0.2, height * 0.3
    distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    
    bloom_mask = distance < 30
    b5[bloom_mask] += np.random.normal(0.08, 0.02, b5[bloom_mask].shape) * (1 - distance[bloom_mask]/30)
    b4[bloom_mask] -= np.random.normal(0.01, 0.005, b4[bloom_mask].shape) * (1 - distance[bloom_mask]/30)
    b3[bloom_mask] += np.random.normal(0.05, 0.01, b3[bloom_mask].shape) * (1 - distance[bloom_mask]/30)
    
    return np.clip(b3, 0, 1), np.clip(b4, 0.01, 1), np.clip(b5, 0, 1), np.clip(b8a, 0, 1)

def mask_to_lake(raster_shape):
    height, width = raster_shape
    y, x = np.ogrid[:height, :width]
    center_x, center_y = width * 0.5, height * 0.5
    mask = ((x - center_x)**2 / (width*0.4)**2) + ((y - center_y)**2 / (height*0.8)**2) <= 1
    return mask

def calculate_ndci(b5, b4):
    return (b5 - b4) / (b5 + b4 + 1e-8)

def calculate_sabi(b4, b3, b8a):
    return (b4 - b3) / (b8a + b3 + 1e-8)

def calculate_chl_proxy(b4, b8a):
    return (b4 / (b8a + 1e-8)) * 10.5

def classify_bloom_risk(ndci):
    classified = np.zeros_like(ndci, dtype=np.uint8)
    classified[ndci < NDCI_THRESHOLDS["no_bloom"]] = 1 
    classified[(ndci >= NDCI_THRESHOLDS["no_bloom"]) & (ndci < NDCI_THRESHOLDS["low"])] = 2
    classified[(ndci >= NDCI_THRESHOLDS["low"]) & (ndci < NDCI_THRESHOLDS["medium"])] = 3
    classified[ndci >= NDCI_THRESHOLDS["medium"]] = 4
    return classified

def raster_to_vector_zones(classified, transform, mask):
    classified = np.where(mask, classified, 0)
    results = []
    for geom, value in shapes(classified, mask=mask, transform=transform):
        val = int(value)
        if val == 0: continue
        risk_map = {1: "no_bloom", 2: "low", 3: "medium", 4: "high"}
        results.append({
            "geometry": shape(geom),
            "properties": {"risk_level": risk_map[val], "class_id": str(val)}
        })
    return results

def save_raster(data, out_path, transform):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    height, width = data.shape
    with rasterio.open(
        out_path, 'w', driver='GTiff', height=height, width=width,
        count=1, dtype=data.dtype, crs='+proj=latlong', transform=transform,
    ) as dst:
        dst.write(data, 1)

def export_geojson(zones, out_path, date_str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if not zones: return
    gdf = gpd.GeoDataFrame.from_features(zones, crs="EPSG:4326")
    gdf['area_sqm'] = gdf.geometry.area * (111000 * 76000)
    gdf['date'] = date_str
    gdf.to_file(out_path, driver="GeoJSON")

def generate_all_visuals(ndci, classified, chl, mask, transform, date_str, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    height, width = ndci.shape
    left = transform.c
    top = transform.f
    right = left + width * transform.a
    bottom = top + height * transform.e
    extent = [left, right, bottom, top]
    
    ndci_masked = np.where(mask, ndci, np.nan)
    class_masked = np.where(mask, classified, np.nan)
    chl_masked = np.where(mask, chl, np.nan)
    
    plt.figure(figsize=(10, 6))
    cmap_risk = ListedColormap(['#add8e6', '#ffe4b5', '#ffa500', '#ff0000'])
    plt.imshow(class_masked, cmap=cmap_risk, vmin=1, vmax=4, extent=extent)
    plt.title(f"Lake Tarnita - Spatial Bloom Risk Map ({date_str})")
    patches = [
        mpatches.Patch(color='#add8e6', label='No Bloom'),
        mpatches.Patch(color='#ffe4b5', label='Low Risk'),
        mpatches.Patch(color='#ffa500', label='Medium Risk'),
        mpatches.Patch(color='#ff0000', label='High Risk')
    ]
    plt.legend(handles=patches, loc='upper right', bbox_to_anchor=(1.25, 1))
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'bloom_map_{date_str}.png'), bbox_inches='tight')
    plt.close()
    
    unique, counts = np.unique(classified[mask], return_counts=True)
    dist = dict(zip(unique, counts))
    labels = ['No Bloom', 'Low Risk', 'Medium Risk', 'High Risk']
    colors = ['#add8e6', '#ffe4b5', '#ffa500', '#ff0000']
    sizes = [dist.get(i, 0) for i in [1, 2, 3, 4]]
    
    plt.figure(figsize=(6, 6))
    if sum(sizes) > 0:
        plt.pie(sizes, labels=[l for i, l in enumerate(labels) if sizes[i]>0], 
                colors=[c for i, c in enumerate(colors) if sizes[i]>0],
                autopct='%1.1f%%', startangle=140)
    plt.title(f"Bloom Risk Area Distribution ({date_str})")
    plt.savefig(os.path.join(output_dir, f'bloom_distribution_{date_str}.png'))
    plt.close()
    
    plt.figure(figsize=(10, 6))
    plt.imshow(ndci_masked, cmap='viridis', extent=extent)
    plt.colorbar(label='NDCI Value')
    plt.title(f"Lake Tarnita - NDCI Heatmap ({date_str})")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'ndci_heatmap_{date_str}.png'))
    plt.close()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    im1 = ax1.imshow(ndci_masked, cmap='viridis', extent=extent)
    ax1.set_title('NDCI')
    ax1.set_xlabel("Longitude")
    ax1.set_ylabel("Latitude")
    fig.colorbar(im1, ax=ax1)
    im2 = ax2.imshow(chl_masked, cmap='plasma', extent=extent)
    ax2.set_title('Chlorophyll-a Proxy')
    ax2.set_xlabel("Longitude")
    ax2.set_ylabel("Latitude")
    fig.colorbar(im2, ax=ax2)
    plt.suptitle(f"NDCI vs Chlorophyll-a Proxy ({date_str})")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'ndci_vs_chl_{date_str}.png'))
    plt.close()
    
    past_dates = ['2026-07-01', '2026-07-15', '2026-08-01', date_str]
    mock_high = [5, 12, 25, (dist.get(4,0)/sum(sizes))*100]
    mock_med = [15, 20, 30, (dist.get(3,0)/sum(sizes))*100]
    mock_low = [30, 40, 25, (dist.get(2,0)/sum(sizes))*100]
    mock_no = [50, 28, 20, (dist.get(1,0)/sum(sizes))*100]
    
    plt.figure(figsize=(10, 6))
    plt.stackplot(past_dates, mock_high, mock_med, mock_low, mock_no, 
                  labels=['High', 'Medium', 'Low', 'No Bloom'],
                  colors=['#ff0000', '#ffa500', '#ffe4b5', '#add8e6'], alpha=0.8)
    plt.title("Temporal Evolution of Bloom Risk Area (%)")
    plt.ylabel("% of Lake Area")
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'bloom_evolution.png'))
    plt.close()
