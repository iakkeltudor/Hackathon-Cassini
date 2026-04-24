from fastapi import APIRouter

router = APIRouter()

@router.get("/bounding-box")
def get_data_in_bbox(min_lon: float, min_lat: float, max_lon: float, max_lat: float):
    return {"message": "Bounding box endpoint placeholder", "bbox": [min_lon, min_lat, max_lon, max_lat]}
