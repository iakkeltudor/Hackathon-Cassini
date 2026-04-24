from fastapi import APIRouter

router = APIRouter()

@router.get("/location/{location_id}")
def get_timeseries_for_location(location_id: str, start_date: str, end_date: str):
    return {"message": f"Time series endpoint placeholder for {location_id}"}
