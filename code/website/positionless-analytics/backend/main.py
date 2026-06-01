"""
FastAPI backend for NBA Positionless Analytics.
Serves CatBoost injury risk predictions + parquet-backed aggregates.

Run:
    uvicorn main:app --reload --port 8000

Deploy to Render/Railway: set PORT env var, gunicorn or uvicorn.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── CatBoost (optional — gracefully degrade if not installed) ──────────────────
try:
    from catboost import CatBoostClassifier
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    logging.warning("catboost not installed; falling back to heuristic predictions.")

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR    = Path(__file__).parent.parent.parent   # project root
MODEL_PATH  = ROOT_DIR / "outputs" / "website-catboost-model.cbm"
PARQUET_PATH= ROOT_DIR / "data" / "Player_Games_Injuries_Travel_Bio.parquet"
JSON_DIR    = ROOT_DIR / "output" / "Website JSONs"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="NBA Positionless Analytics API",
    description="Backend for positionless index and injury risk predictions.",
    version="1.0.0",
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Feature config (must match frontend FEATURES list) ────────────────────────
FEATURE_NAMES = [
    "rolling_7g_three_pointers_attempted",
    "rolling_7g_rebounds",
    "rolling_7g_USG",
    "positionless_index",
    "rolling_7g_blocks",
    "winPercent_team",
    "rolling_7g_points_per36",
    "rolling_7g_minutes",
    "games_last_14d",
    "rolling_7g_assists_per36",
]

# Rough importance weights for SHAP approximation when model is offline
FEATURE_WEIGHTS = {
    "rolling_7g_minutes":               0.22,
    "rolling_7g_USG":                   0.18,
    "games_last_14d":                   0.14,
    "rolling_7g_points_per36":          0.11,
    "positionless_index":               0.10,
    "rolling_7g_rebounds":              0.08,
    "rolling_7g_three_pointers_attempted": 0.06,
    "winPercent_team":                  0.05,
    "rolling_7g_assists_per36":         0.04,
    "rolling_7g_blocks":                0.02,
}

# ── Load model on startup ─────────────────────────────────────────────────────
model: Optional[Any] = None

@app.on_event("startup")
def load_model():
    global model
    if not CATBOOST_AVAILABLE:
        logger.warning("CatBoost not available.")
        return
    if not MODEL_PATH.exists():
        logger.warning(f"Model not found at {MODEL_PATH}")
        return
    try:
        model = CatBoostClassifier()
        model.load_model(str(MODEL_PATH))
        logger.info(f"Loaded CatBoost model from {MODEL_PATH}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        model = None

# ── Schemas ───────────────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    features: Dict[str, float]

class ShapValue(BaseModel):
    key:   str
    label: str
    value: float

class PredictResponse(BaseModel):
    injury_probability: float
    risk_label:         str
    shap_values:        List[ShapValue]
    model_used:         str

# ── Helpers ───────────────────────────────────────────────────────────────────
_FEATURE_RANGES = {
    "rolling_7g_three_pointers_attempted": (0, 12),
    "rolling_7g_rebounds":                 (0, 16),
    "rolling_7g_USG":                      (0, 45),
    "positionless_index":                  (0, 1),
    "rolling_7g_blocks":                   (0, 4),
    "winPercent_team":                     (0, 100),
    "rolling_7g_points_per36":             (0, 40),
    "rolling_7g_minutes":                  (0, 42),
    "games_last_14d":                      (0, 10),
    "rolling_7g_assists_per36":            (0, 14),
}

def heuristic_predict(features: Dict[str, float]) -> float:
    """Simple weighted heuristic when model is unavailable."""
    score = 0.0
    for key, w in FEATURE_WEIGHTS.items():
        lo, hi = _FEATURE_RANGES.get(key, (0, 1))
        norm = (features.get(key, (lo + hi) / 2) - lo) / max(hi - lo, 1e-6)
        score += norm * w
    # Invert win% (losing teams = more risk)
    wp = features.get("winPercent_team", 50)
    score += ((100 - wp) / 100) * 0.05
    prob = float(np.clip(score * 0.75 + 0.08, 0.02, 0.97))
    return prob

def compute_shap_approx(features: Dict[str, float], probability: float) -> List[ShapValue]:
    base = 0.15
    ranges = _FEATURE_RANGES
    results = []
    for key, w in FEATURE_WEIGHTS.items():
        lo, hi = ranges.get(key, (0, 1))
        mid  = (lo + hi) / 2
        norm = (features.get(key, mid) - mid) / max(hi - lo, 1e-6)
        val  = float(norm * w * (probability - base) * 2)
        results.append(ShapValue(key=key, label=key.replace("rolling_7g_", "").replace("_", " ").title(), value=val))
    return sorted(results, key=lambda x: abs(x.value), reverse=True)[:8]

def risk_label(p: float) -> str:
    if p < 0.25: return "LOW"
    if p < 0.50: return "MODERATE"
    if p < 0.75: return "HIGH"
    return "VERY HIGH"

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status":           "ok",
        "model_loaded":     model is not None,
        "catboost_available": CATBOOST_AVAILABLE,
    }

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    features = req.features

    # Validate all required features are present
    missing = [f for f in FEATURE_NAMES if f not in features]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing features: {missing}")

    if model is not None:
        # Real CatBoost prediction
        try:
            X = pd.DataFrame([{k: features[k] for k in FEATURE_NAMES}])
            proba = model.predict_proba(X)[0]
            # proba is [P(no injury), P(injury)]
            prob = float(proba[1]) if len(proba) > 1 else float(proba[0])

            # Try to get real SHAP values
            try:
                from catboost import Pool
                pool = Pool(X)
                shap_vals = model.get_feature_importance(pool, type="ShapValues")
                # shap_vals shape: (n_samples, n_features + 1) — last col is baseline
                sv = shap_vals[0][:-1]
                shap_out = [
                    ShapValue(
                        key=FEATURE_NAMES[i],
                        label=FEATURE_NAMES[i].replace("rolling_7g_", "").replace("_", " ").title(),
                        value=float(sv[i])
                    )
                    for i in range(len(FEATURE_NAMES))
                ]
                shap_out = sorted(shap_out, key=lambda x: abs(x.value), reverse=True)[:8]
            except Exception as shap_e:
                logger.warning(f"SHAP computation failed: {shap_e}")
                shap_out = compute_shap_approx(features, prob)

            model_used = "catboost"
        except Exception as e:
            logger.error(f"Model inference failed: {e}")
            prob      = heuristic_predict(features)
            shap_out  = compute_shap_approx(features, prob)
            model_used = "heuristic_fallback"
    else:
        prob      = heuristic_predict(features)
        shap_out  = compute_shap_approx(features, prob)
        model_used = "heuristic"

    return PredictResponse(
        injury_probability=prob,
        risk_label=risk_label(prob),
        shap_values=shap_out,
        model_used=model_used,
    )

@app.get("/data/{filename}")
def serve_json(filename: str):
    """Serve precomputed JSON files (fallback if not serving via static files)."""
    allowed = {
        "players_index_table.json",
        "positionless_over_time.json",
        "player_trajectories.json",
        "dashboard_aggregates.json",
    }
    if filename not in allowed:
        raise HTTPException(status_code=404, detail="File not found")
    path = JSON_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found on server")
    return json.loads(path.read_text())