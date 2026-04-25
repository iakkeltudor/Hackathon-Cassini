"""
Sentinel-2 real data ingestion for Lacul Tarnița.

Tries two paths in order:
  1. sentinelhub-py Process API via CDSE endpoint
     → fast, lightweight (requires CDSE_CLIENT_ID + CDSE_CLIENT_SECRET)
  2. CDSE OData catalogue + Keycloak auth, downloading only the individual
     band JP2 files (B03/B04/B05 at 20 m) instead of full SAFE archives
     → works with existing CDSE_USER + CDSE_PASSWORD

Outputs: storage/processed/eo_clean.csv
Columns: date, cloud_cover, ndci_mean, chl_proxy_mean,
         turbidity_proxy_mean, tsm_mean, source
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

_ENV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(_ENV)

# ── AOI ───────────────────────────────────────────────────────────────────────
# Bounding box: [W, S, E, N] in WGS-84
LAKE_BBOX = [23.200, 46.690, 23.320, 46.730]

# Evalscript: computes NDCI, Chl-a proxy, turbidity proxy, TSM in one pass
EVALSCRIPT = """
//VERSION=3
function setup() {
  return {
    input:  [{bands: ["B03","B04","B05","B8A"], units: "REFLECTANCE"}],
    output: [{id: "indices", bands: 4, sampleType: "FLOAT32"}]
  };
}
function evaluatePixel(s) {
  var eps = 1e-8;
  var ndci      = (s.B05 - s.B04) / (s.B05 + s.B04 + eps);
  var chl       = (s.B05 / (s.B04 + eps)) * 10.5;
  var turbidity = (s.B04 / (s.B03 + eps)) * 15.0;
  var tsm       = s.B04 * 2.5 + 5.0;
  return [ndci, chl, turbidity, tsm];
}
"""


# ─────────────────────────────────────────────────────────────────────────────
# PATH 1 — Sentinel Hub Process API (sentinelhub-py, CDSE endpoint)
# ─────────────────────────────────────────────────────────────────────────────

def _try_sentinelhub_path(start_date: str, end_date: str, max_cloud: int) -> bool:
    client_id     = os.environ.get("CDSE_CLIENT_ID",     "").strip()
    client_secret = os.environ.get("CDSE_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        print("  [SH path] CDSE_CLIENT_ID / CDSE_CLIENT_SECRET not configured — skipped.")
        return False

    try:
        from sentinelhub import (
            SHConfig, BBox, CRS, DataCollection,
            SentinelHubCatalog, SentinelHubRequest, MimeType,
        )
    except ImportError:
        print("  [SH path] 'sentinelhub' not installed — skipped.")
        return False

    cfg = SHConfig()
    cfg.sh_client_id     = client_id
    cfg.sh_client_secret = client_secret
    cfg.sh_base_url      = "https://sh.dataspace.copernicus.eu"
    cfg.sh_token_url     = (
        "https://identity.dataspace.copernicus.eu"
        "/auth/realms/CDSE/protocol/openid-connect/token"
    )

    S2_CDSE = DataCollection.SENTINEL2_L2A.define_from(
        "S2L2A_CDSE", service_url="https://sh.dataspace.copernicus.eu"
    )
    bbox = BBox(LAKE_BBOX, crs=CRS.WGS84)

    print(f"  [SH path] Querying CDSE catalog {start_date} → {end_date} …")
    try:
        catalog  = SentinelHubCatalog(config=cfg)
        items    = list(catalog.search(
            collection=S2_CDSE,
            bbox=bbox,
            time=(start_date, end_date),
            filter=f"eo:cloud_cover < {max_cloud}",
            fields={"include": ["id", "properties.datetime", "properties.eo:cloud_cover"]},
        ))
    except Exception as exc:
        print(f"  [SH path] Catalog query failed: {exc}")
        return False

    if not items:
        print("  [SH path] No scenes returned.")
        return False

    print(f"  [SH path] {len(items)} scenes found. Fetching band means …")
    rows       = []
    seen_dates: set[str] = set()

    for item in sorted(items, key=lambda x: x["properties"]["datetime"]):
        dt_str = item["properties"]["datetime"][:10]
        if dt_str in seen_dates:
            continue
        seen_dates.add(dt_str)

        try:
            req = SentinelHubRequest(
                evalscript=EVALSCRIPT,
                input_data=[SentinelHubRequest.input_data(
                    data_collection=S2_CDSE,
                    time_interval=(dt_str, dt_str),
                    other_args={"dataFilter": {"maxCloudCoverage": max_cloud}},
                )],
                responses=[SentinelHubRequest.output_response("indices", MimeType.TIFF)],
                bbox=bbox,
                size=(40, 80),
                config=cfg,
            )
            data = req.get_data()[0]          # shape (H, W, 4)
        except Exception as exc:
            print(f"    {dt_str}: {exc}")
            continue

        if data is None or data.size == 0:
            continue
        valid = data[:, :, 0] > -1
        if valid.sum() == 0:
            continue

        rows.append({
            "date":                 datetime.strptime(dt_str, "%Y-%m-%d"),
            "cloud_cover":          item["properties"].get("eo:cloud_cover", 0),
            "ndci_mean":            float(np.nanmean(data[:, :, 0][valid])),
            "chl_proxy_mean":       float(np.nanmean(data[:, :, 1][valid])),
            "turbidity_proxy_mean": float(np.nanmean(data[:, :, 2][valid])),
            "tsm_mean":             float(np.nanmean(data[:, :, 3][valid])),
            "source":               "sentinel2_sh",
        })

    if not rows:
        print("  [SH path] No valid data after processing.")
        return False

    _save_eo(rows)
    return True


# ─────────────────────────────────────────────────────────────────────────────
# PATH 2 — CDSE OData + Keycloak (download only JP2 band files)
# ─────────────────────────────────────────────────────────────────────────────

def _try_odata_path(start_date: str, end_date: str, max_cloud: int) -> bool:
    user     = os.environ.get("CDSE_USER",     "").strip()
    password = os.environ.get("CDSE_PASSWORD", "").strip()

    if not user or not password:
        print("  [OData path] CDSE_USER / CDSE_PASSWORD not configured — skipped.")
        return False

    try:
        import requests as _req
        import rasterio
        import rasterio.mask
        import geopandas as gpd
    except ImportError as exc:
        print(f"  [OData path] Missing package ({exc}) — skipped.")
        return False

    # ── Keycloak authentication ──────────────────────────────────────────────
    print("  [OData path] Authenticating with Keycloak …")
    tok_resp = _req.post(
        "https://identity.dataspace.copernicus.eu"
        "/auth/realms/CDSE/protocol/openid-connect/token",
        data={
            "client_id":  "cdse-public",
            "username":   user,
            "password":   password,
            "grant_type": "password",
        },
        timeout=30,
    )
    if tok_resp.status_code != 200:
        print(f"  [OData path] Auth failed ({tok_resp.status_code}): {tok_resp.text[:300]}")
        return False

    token   = tok_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ── OData product search ─────────────────────────────────────────────────
    W, S, E, N = LAKE_BBOX
    wkt = f"POLYGON (({W} {S},{E} {S},{E} {N},{W} {N},{W} {S}))"
    odata_url = (
        "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
        "?$filter="
        "Collection/Name eq 'SENTINEL-2'"
        f" and OData.CSC.Intersects(area=geography'SRID=4326;{wkt}')"
        f" and ContentDate/Start ge {start_date}T00:00:00.000Z"
        f" and ContentDate/Start le {end_date}T23:59:59.000Z"
        " and Attributes/OData.CSC.StringAttribute/any("
        "att:att/Name eq 'productType'"
        " and att/OData.CSC.StringAttribute/Value eq 'S2MSI2A')"
        "&$top=50&$expand=Attributes"
    )

    print("  [OData path] Querying product catalogue …")
    try:
        resp = _req.get(odata_url, timeout=60)
        resp.raise_for_status()
        products = resp.json().get("value", [])
    except Exception as exc:
        print(f"  [OData path] Catalogue query failed: {exc}")
        return False

    def _cloud(p: dict) -> float:
        for a in p.get("Attributes", []):
            if a.get("Name") == "cloudCover":
                return float(a.get("Value", 100))
        return 100.0

    products = [p for p in products if _cloud(p) <= max_cloud]
    products.sort(key=lambda p: p["Name"])
    print(f"  [OData path] {len(products)} scenes ≤ {max_cloud}% cloud.")

    if not products:
        return False

    # ── Lake geometry for band masking ───────────────────────────────────────
    boundary = os.path.join(config.STORAGE_DIR, "layers", "tarnita_lake_boundary.geojson")
    lake_geoms = None
    if os.path.exists(boundary):
        gdf = gpd.read_file(boundary)
        if not gdf.empty:
            lake_geoms = gdf.to_crs("EPSG:32634").geometry.values  # UTM for masking

    sentinel_dir = os.path.join(config.RAW_DIR, "sentinel")
    os.makedirs(sentinel_dir, exist_ok=True)

    rows: list[dict] = []
    seen_dates: set[str] = set()

    for product in products:
        pid   = product["Id"]
        pname = product["Name"]
        # Date embedded in name: S2A_MSIL2A_YYYYMMDDTHHMMSS_...
        try:
            date_str = pname.split("_")[2][:8]
        except IndexError:
            continue
        if date_str in seen_dates:
            continue
        seen_dates.add(date_str)
        date_obj = datetime.strptime(date_str, "%Y%m%d")

        print(f"  [{date_obj.date()}] {pname[:55]} …", end=" ", flush=True)

        # Get granule node name
        try:
            gran_url = (
                f"https://catalogue.dataspace.copernicus.eu/odata/v1"
                f"/Products({pid})/Nodes({pname}.SAFE)/Nodes(GRANULE)"
            )
            gran_resp = _req.get(gran_url, headers=headers, timeout=30)
            gran_resp.raise_for_status()
            granules = gran_resp.json().get("value", [])
            if not granules:
                print("no granule node")
                continue
            granule_name = granules[0]["Name"]
        except Exception as exc:
            print(f"node error: {exc}")
            continue

        bands_data: dict[str, np.ndarray] = {}
        for band in ("B03", "B04", "B05"):
            for res, suffix in (("R20m", "20m"), ("R10m", "10m")):
                try:
                    files_url = (
                        f"https://catalogue.dataspace.copernicus.eu/odata/v1"
                        f"/Products({pid})/Nodes({pname}.SAFE)"
                        f"/Nodes(GRANULE)/Nodes({granule_name})"
                        f"/Nodes(IMG_DATA)/Nodes({res})"
                    )
                    f_resp = _req.get(files_url, headers=headers, timeout=30)
                    f_resp.raise_for_status()
                    files = f_resp.json().get("value", [])
                    band_file = next(
                        (f["Name"] for f in files if f"_{band}_{suffix}" in f["Name"]),
                        None,
                    )
                    if not band_file:
                        continue

                    dl_url = (
                        f"https://catalogue.dataspace.copernicus.eu/odata/v1"
                        f"/Products({pid})/Nodes({pname}.SAFE)"
                        f"/Nodes(GRANULE)/Nodes({granule_name})"
                        f"/Nodes(IMG_DATA)/Nodes({res})/Nodes({band_file})/$value"
                    )
                    local = os.path.join(sentinel_dir, f"{date_str}_{band}_{res}.jp2")
                    if not os.path.exists(local):
                        with _req.get(dl_url, headers=headers, stream=True, timeout=600) as r:
                            r.raise_for_status()
                            with open(local, "wb") as fout:
                                for chunk in r.iter_content(chunk_size=65536):
                                    fout.write(chunk)

                    with rasterio.open(local) as src:
                        if lake_geoms is not None:
                            try:
                                # Reproject geoms to raster CRS on the fly
                                from shapely.ops import transform as _stransform
                                import pyproj
                                transformer = pyproj.Transformer.from_crs(
                                    "EPSG:4326", src.crs.to_epsg(), always_xy=True
                                )
                                from shapely.geometry import mapping as _mapping
                                geoms_proj = [
                                    _stransform(transformer.transform, g)
                                    for g in gpd.read_file(boundary).geometry.values
                                ]
                                out, _ = rasterio.mask.mask(src, geoms_proj, crop=True, nodata=0)
                                pixels = out[0][out[0] > 0].astype(float) / 10000.0
                            except Exception:
                                pixels = src.read(1).flatten().astype(float) / 10000.0
                                pixels = pixels[pixels > 0]
                        else:
                            pixels = src.read(1).flatten().astype(float) / 10000.0
                            pixels = pixels[pixels > 0]

                    if pixels.size > 0:
                        bands_data[band] = pixels
                    break  # got this band
                except Exception:
                    continue

        if "B04" not in bands_data:
            print("no B04")
            continue

        eps = 1e-8
        b3  = float(np.mean(bands_data.get("B03", np.array([0.04]))))
        b4  = float(np.mean(bands_data["B04"]))
        b5  = float(np.mean(bands_data.get("B05", np.array([0.04]))))

        rows.append({
            "date":                 date_obj,
            "cloud_cover":          _cloud(product),
            "ndci_mean":            (b5 - b4) / (b5 + b4 + eps),
            "chl_proxy_mean":       (b5 / (b4 + eps)) * 10.5,
            "turbidity_proxy_mean": (b4 / (b3 + eps)) * 15.0,
            "tsm_mean":             b4 * 2.5 + 5.0,
            "source":               "sentinel2_odata",
        })
        print("ok")

    if not rows:
        print("  [OData path] No scenes could be processed.")
        return False

    _save_eo(rows)
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _save_eo(rows: list[dict]) -> None:
    df = pd.DataFrame(rows).sort_values("date")
    os.makedirs(config.PROCESSED_DIR, exist_ok=True)
    out = os.path.join(config.PROCESSED_DIR, "eo_clean.csv")
    df.to_csv(out, index=False)
    print(f"\n  ✓ Saved {len(df)} EO scenes → {out}")


def ingest_sentinel_data(
    start_date: str | None = None,
    end_date:   str | None = None,
    max_cloud:  int        = 20,
) -> bool:
    """
    Orchestrate Sentinel-2 ingestion. Returns True if EO data was produced.
    """
    load_dotenv(_ENV)
    start  = start_date or os.environ.get("TARNITA_START_DATE", "2023-06-01")
    end    = end_date   or os.environ.get("TARNITA_END_DATE",   "2024-09-30")
    cloud  = int(os.environ.get("MAX_CLOUD_COVER", str(max_cloud)))

    print(f"\n{'='*55}")
    print(f"  Sentinel-2 ingestion: {start} → {end}  cloud≤{cloud}%")
    print(f"{'='*55}")

    if _try_sentinelhub_path(start, end, cloud):
        return True
    if _try_odata_path(start, end, cloud):
        return True

    print(
        "\n  ✗ All ingestion paths failed.\n"
        "  To use Sentinel Hub API:  set CDSE_CLIENT_ID + CDSE_CLIENT_SECRET\n"
        "    (create at https://shapps.dataspace.copernicus.eu/dashboard/#/account/settings)\n"
        "  To use OData download:    set CDSE_USER + CDSE_PASSWORD\n"
        "  Existing eo_clean.csv will be used if present."
    )
    return False


if __name__ == "__main__":
    ingest_sentinel_data()
