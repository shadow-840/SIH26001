from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import logging
import os
import concurrent.futures

# Absolute imports based on your new directory structure
from wrappers.pipeline_aggregator import collect_all_geospatial_data
from alert_system.alert_engine import LandslideRiskEvaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FastAPI_Main")

app = FastAPI(title="SIH26001 Landslide Early Warning System API")

# Allow Web Dashboard to call this API without CORS blocking
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

evaluator = LandslideRiskEvaluator()

class CoordinateRequest(BaseModel):
    latitude: float
    longitude: float

@app.post("/api/v1/analyze-risk")
def analyze_risk(location: CoordinateRequest):
    """
    Main endpoint for Android app.
    Takes lat/lon and returns the full empirical risk assessment.
    """
    try:
        # 1. Run Data Ingestion Pipeline
        raw_data = collect_all_geospatial_data(location.latitude, location.longitude)
        
        if not raw_data:
            raise HTTPException(status_code=500, detail="Failed to collect geospatial data.")

        # 2. Run Real-Time Empirical Engine (Physics + Thresholds)
        realtime_alert = evaluator.evaluate_realtime_empirical(raw_data)
        
        # 3. Return Unified Payload
        return {
            "status": "success",
            "meta": raw_data["meta"],
            "geomorphology": raw_data["geomorphology"],
            "realtime_empirical_alert": realtime_alert
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/district-macro")
def get_district_macro():
    """
    Multithreaded endpoint for Web Dashboard to display high-level state/district status.
    Fetches all locations concurrently to eliminate loading bottlenecks.
    """
    districts = [
        {"name": "Dima Hasao", "state": "Assam", "lat": 25.1833, "lon": 93.0333},
        {"name": "Cachar (Barak Valley)", "state": "Assam", "lat": 24.8333, "lon": 92.7778},
        {"name": "Tawang", "state": "Arunachal Pradesh", "lat": 27.5833, "lon": 91.8667},
        {"name": "Dibang Valley", "state": "Arunachal Pradesh", "lat": 28.7954, "lon": 95.9667},
        {"name": "Noney", "state": "Manipur", "lat": 24.8167, "lon": 93.6167},
        {"name": "Senapati", "state": "Manipur", "lat": 25.2667, "lon": 94.0167},
        {"name": "Kohima", "state": "Nagaland", "lat": 25.6751, "lon": 94.1086},
        {"name": "Cherrapunji Belt", "state": "Meghalaya", "lat": 25.2736, "lon": 91.7323},
        {"name": "East Khasi Hills", "state": "Meghalaya", "lat": 25.5788, "lon": 91.8933},
        {"name": "Aizawl", "state": "Mizoram", "lat": 23.7271, "lon": 92.7176},
        {"name": "Dhalai", "state": "Tripura", "lat": 23.8667, "lon": 91.9444},
        {"name": "Mangan", "state": "Sikkim", "lat": 27.4950, "lon": 88.5340}
    ]
    
    def fetch_single_district(d):
        try:
            data = collect_all_geospatial_data(d["lat"], d["lon"])
            if data:
                realtime = evaluator.evaluate_realtime_empirical(data)
                return {
                    "district": d["name"],
                    "state": d["state"],
                    "coordinates": {"lat": d["lat"], "lon": d["lon"]},
                    "current_status": realtime["level"],
                    "color": realtime["color"]
                }
        except Exception as e:
            logger.error(f"Failed to process district {d['name']}: {e}")
        return None

    results = []
    # Fire all 12 requests at the exact same time
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(fetch_single_district, d) for d in districts]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
            
    return {"ner_macro_overview": results}

# ==========================================
# MOUNT FRONTEND DASHBOARD
# ==========================================
# Dynamically find the path to the dashboard folder
current_file_path = os.path.dirname(os.path.abspath(__file__))      # .../backend/api
backend_root = os.path.dirname(current_file_path)                   # .../backend
project_root = os.path.dirname(backend_root)                        # .../SIH26001
dashboard_path = os.path.join(project_root, "dashboard")            # .../SIH26001/dashboard

# Mount the dashboard directory at the root URL ("/")
app.mount("/", StaticFiles(directory=dashboard_path, html=True), name="dashboard")

if __name__ == "__main__":
    # Note: When running from the root 'backend' folder, 
    # use the command `uvicorn api.main:app --reload` instead of executing this directly.
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)