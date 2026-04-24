from fastapi import APIRouter

router = APIRouter()

@router.get("/latest")
def get_latest_indicators():
    return {"message": "Latest indicators endpoint placeholder"}
