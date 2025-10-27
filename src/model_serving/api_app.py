import sys
import os
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, 'src'))

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from src.model_serving.prediction_logic import PredictionLogic
from src.utils.logging_setup import setup_logging
from src.utils.config_reader import ConfigReader

logger = setup_logging(__name__)
config = ConfigReader(env=os.getenv("APP_ENV", "dev"))

app = FastAPI(
    title="Snapp Real-Time Demand Forecasting API",
    description="API for predicting ride demand in real-time.",
    version="1.0.0",
)

prediction_logic_instance: PredictionLogic = None

@app.on_event("startup")
async def startup_event():
    global prediction_logic_instance
    try:
        prediction_logic_instance = PredictionLogic(env=os.getenv("APP_ENV", "dev"))
        logger.info("PredictionLogic initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize PredictionLogic: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load prediction model.")

class FeatureSet(BaseModel):
    hour_of_day: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    is_weekend: int = Field(..., ge=0, le=1)
    is_holiday: int = Field(..., ge=0, le=1)
    peak_hour_indicator: int = Field(..., ge=0, le=1)
    demand_last_15min: float = Field(..., ge=0)
    demand_last_30min: float = Field(..., ge=0)
    demand_last_60min: float = Field(..., ge=0)
    demand_last_1440min: float = Field(..., ge=0)

class SinglePredictionResponse(BaseModel):
    predicted_demand: float = Field(..., description="Predicted number of rides in the next 15 minutes.")

class BatchPredictionResponse(BaseModel):
    predictions: List[float] = Field(..., description="List of predicted demands.")

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok", "message": "API is healthy and model is loaded." if prediction_logic_instance else "API is healthy, but model loading failed."}

@app.post("/predict_single", response_model=SinglePredictionResponse, status_code=status.HTTP_200_OK)
async def predict_single_demand(features: FeatureSet):
    if not prediction_logic_instance:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Prediction service not initialized.")
    try:
        prediction = prediction_logic_instance.predict_demand(features.model_dump())
        return SinglePredictionResponse(predicted_demand=prediction)
    except Exception as e:
        logger.exception("Error during single prediction:")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Prediction failed: {e}")

@app.post("/predict_batch", response_model=BatchPredictionResponse, status_code=status.HTTP_200_OK)
async def predict_batch_demand(features_list: List[FeatureSet]):
    if not prediction_logic_instance:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Prediction service not initialized.")
    try:
        features_dicts = [f.model_dump() for f in features_list]
        predictions = prediction_logic_instance.batch_predict_demand(features_dicts)
        return BatchPredictionResponse(predictions=predictions)
    except Exception as e:
        logger.exception("Error during batch prediction:")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Batch prediction failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn_host = config.get("inference_api.host")
    uvicorn_port = config.get("inference_api.port")
    logger.info(f"Starting Uvicorn server on {uvicorn_host}:{uvicorn_port}")
    uvicorn.run(app, host=uvicorn_host, port=uvicorn_port)
