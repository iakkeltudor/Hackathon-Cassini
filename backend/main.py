from fastapi import FastAPI
from api.routers import geospatial, timeseries, indicators

app = FastAPI(
    title="Water Pollution Monitoring Platform API",
    description="API for accessing spatial-temporal water quality data, Copernicus EO data, and ML inference results.",
    version="1.0.0"
)

app.include_router(geospatial.router, prefix="/api/v1/geospatial", tags=["Geospatial"])
app.include_router(timeseries.router, prefix="/api/v1/timeseries", tags=["Time Series"])
app.include_router(indicators.router, prefix="/api/v1/indicators", tags=["Indicators"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Water Pollution Monitoring API"}
