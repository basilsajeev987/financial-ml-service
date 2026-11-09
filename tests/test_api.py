
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


# Load model feature names
BASE_DIR = Path(__file__).resolve().parent.parent
FEATURES_PATH = BASE_DIR / "models" / "feature_columns.json"

with open(FEATURES_PATH, "r", encoding="utf-8") as file:
    FEATURE_COLUMNS = json.load(file)


# Test client fixture
@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# Test 1: Root endpoint
def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


# Test 2: Health endpoint
def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["model_loaded"] is True


# Test 3: Model information
def test_model_info(client):
    response = client.get("/model/info")

    assert response.status_code == 200

    result = response.json()

    assert result["features_count"] == 26
    assert len(result["features"]) == 26


# Test 4: Successful prediction
def test_successful_prediction(client):

    features = {
        feature: 0.0
        for feature in FEATURE_COLUMNS
    }

    payload = {
        "ticker": "BTC-USD",
        "features": features
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200

    result = response.json()

    assert result["status"] == "success"
    assert result["prediction"] in ["UP", "DOWN"]

    assert 0 <= result["probability_up"] <= 1
    assert 0 <= result["probability_down"] <= 1


# Test 5: Missing feature validation
def test_missing_feature_rejected(client):

    features = {
        feature: 0.0
        for feature in FEATURE_COLUMNS
    }

    features.pop(FEATURE_COLUMNS[0])

    payload = {
        "ticker": "BTC-USD",
        "features": features
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 422
