
import json
import math
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"

MODEL_PATH = MODEL_DIR / "ai_model.pkl"
FEATURES_PATH = MODEL_DIR / "feature_columns.json"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("financial-ml-service")

model = None
feature_columns = []
metadata = {}


# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------

def load_artifacts():
    global model, feature_columns, metadata

    required_files = [MODEL_PATH, FEATURES_PATH, METADATA_PATH]

    for file_path in required_files:
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required model artifact not found: {file_path}"
            )

    model = joblib.load(MODEL_PATH)

    with open(FEATURES_PATH, "r", encoding="utf-8") as file:
        feature_columns = json.load(file)

    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    if not isinstance(feature_columns, list) or not feature_columns:
        raise ValueError("feature_columns.json must contain a non-empty list")

    if len(feature_columns) != len(set(feature_columns)):
        raise ValueError("Duplicate feature names found")

    if not hasattr(model, "predict") or not hasattr(model, "predict_proba"):
        raise ValueError("Model must support predict and predict_proba")

    logger.info("Model loaded successfully")
    logger.info("Number of features: %s", len(feature_columns))


# --------------------------------------------------
# API LIFECYCLE
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_artifacts()
    yield
    logger.info("Financial ML API shutting down")


# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="Financial ML Prediction API",
    description="Production-style financial machine learning inference service",
    version="1.0.0",
    lifespan=lifespan
)


# --------------------------------------------------
# REQUEST SCHEMA
# --------------------------------------------------

class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(default="BTC-USD", min_length=1, max_length=20)
    features: dict[str, float]


# --------------------------------------------------
# ROOT ENDPOINT
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "service": "Financial ML Prediction API",
        "status": "running",
        "version": "1.0.0",
        "documentation": "/docs"
    }


# --------------------------------------------------
# HEALTH ENDPOINT
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy" if model is not None else "unavailable",
        "model_loaded": model is not None
    }


# --------------------------------------------------
# MODEL INFORMATION
# --------------------------------------------------

@app.get("/model/info")
def model_info():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {
        "model_type": type(model).__name__,
        "model_name": metadata.get("model_name", "XGBoost"),
        "model_version": metadata.get("model_version", "1.0.0"),
        "features_count": len(feature_columns),
        "features": feature_columns,
        "metadata": metadata
    }


# --------------------------------------------------
# PREDICTION ENDPOINT
# --------------------------------------------------

@app.post("/predict")
def predict(request: PredictionRequest):

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Prediction model is not available"
        )

    supplied_features = request.features

    missing_features = [
        feature for feature in feature_columns
        if feature not in supplied_features
    ]

    extra_features = [
        feature for feature in supplied_features
        if feature not in feature_columns
    ]

    if missing_features or extra_features:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Feature validation failed",
                "missing_features": missing_features,
                "unexpected_features": extra_features
            }
        )

    values = []

    for feature in feature_columns:
        value = supplied_features[feature]

        if not math.isfinite(value):
            raise HTTPException(
                status_code=422,
                detail=f"Feature '{feature}' must be a finite number"
            )

        values.append(value)

    try:
        input_data = pd.DataFrame(
            [values],
            columns=feature_columns
        )

        prediction = int(model.predict(input_data)[0])
        probabilities = model.predict_proba(input_data)[0]

        probability_down = float(probabilities[0])
        probability_up = float(probabilities[1])

        result = "UP" if prediction == 1 else "DOWN"

        return {
            "status": "success",
            "ticker": request.ticker.upper(),
            "prediction": result,
            "probability_up": round(probability_up, 6),
            "probability_down": round(probability_down, 6),
            "model": metadata.get("model_name", "XGBoost"),
            "model_version": metadata.get("model_version", "1.0.0")
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Prediction failed")

        raise HTTPException(
            status_code=500,
            detail="Internal prediction error"
        )
