from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from services.alerting import send_alert_notification
from services.feature_store import insert_feature, get_last_aqi, fetch_features_dataframe
from services.features import compute_features
from services.model_registry import load_latest_model
from routers.openweather import _fetch_weather, _fetch_air_quality
from trainers.train import train_and_register_model

import asyncio
import numpy as np
from typing import Optional, Any


def _sanitize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _sanitize_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_json(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and np.isnan(value):
        return None
    return value

predict_router = APIRouter(tags=['predict'])
FEATURE_COLUMNS = ['temp', 'humidity', 'pressure', 'wind_speed', 'pm2_5', 'pm10', 'no2', 'o3', 'hour', 'day', 'month']


@predict_router.post('/features/fetch')
async def fetch_and_store(city: str = Query(..., min_length=1)):
    api_key = __import__('os').environ.get('OPEN_WEATHER_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='OPEN_WEATHER_API_KEY not set')

    weather = await asyncio.to_thread(_fetch_weather, city, api_key)
    coord = weather.get('coord', {})
    lat = coord.get('lat')
    lon = coord.get('lon')
    if lat is None or lon is None:
        raise HTTPException(status_code=500, detail='No coordinates')

    air = await asyncio.to_thread(_fetch_air_quality, lat, lon, api_key)
    features = compute_features(city, weather, air)
    insert_feature(features)
    return {'status': 'stored', 'features': features}


@predict_router.post('/features/backfill')
async def backfill(city: str = Query(..., min_length=1), days: Optional[int] = Query(1)):
    results = []
    for i in range(max(1, days)):
        res = await fetch_and_store(city)
        results.append(res)
    return {'status': 'backfilled', 'count': len(results), 'details': results}


@predict_router.post('/train')
async def train():
    try:
        result = await asyncio.to_thread(train_and_register_model)
        return {'status': 'trained', 'result': result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@predict_router.get('/predict')
async def predict(city: str = Query(..., min_length=1)):
    model = load_latest_model()
    if model is None:
        raise HTTPException(status_code=404, detail='No model available')

    df = fetch_features_dataframe()
    if df.empty:
        raise HTTPException(status_code=404, detail='No stored features')

    city_df = df[df['city'] == city].sort_values('timestamp', ascending=False)
    if city_df.empty:
        raise HTTPException(status_code=404, detail='No features for city')

    record = city_df.iloc[0]
    X = [float(record.get(col) or 0) for col in FEATURE_COLUMNS]
    pred = model.predict([X])[0]
    return {'city': city, 'predicted_aqi': float(pred)}


@predict_router.get('/alerts')
async def alerts(city: str = Query(..., min_length=1), threshold: int = Query(4)):
    last = get_last_aqi(city)
    if last is None:
        return {'city': city, 'alert': False, 'reason': 'no data'}

    alert = last >= threshold
    if alert:
        send_alert_notification(city, last, threshold)
    return {'city': city, 'alert': bool(alert), 'aqi': last}


@predict_router.get('/eda')
async def eda():
    df = fetch_features_dataframe()
    if df.empty:
        raise HTTPException(status_code=404, detail='No features stored yet')

    numeric = df.select_dtypes(include=['number'])
    summary = _sanitize_json(numeric.describe().to_dict())
    correlation = _sanitize_json(numeric.corr().to_dict())
    return {
        'samples': len(df),
        'summary': summary,
        'correlation': correlation,
    }


@predict_router.get('/explain')
async def explain(city: str = Query(..., min_length=1)):
    model = load_latest_model()
    if model is None:
        raise HTTPException(status_code=404, detail='No model available')

    df = fetch_features_dataframe()
    if df.empty:
        raise HTTPException(status_code=404, detail='No features stored yet')

    city_df = df[df['city'] == city].sort_values('timestamp', ascending=False)
    if city_df.empty:
        raise HTTPException(status_code=404, detail='No features for city')

    sample = city_df.iloc[0:1]
    X = sample[FEATURE_COLUMNS].fillna(0)
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        base_value = float(explainer.expected_value)
        return {
            'city': city,
            'base_value': base_value,
            'feature_names': FEATURE_COLUMNS,
            'feature_values': X.iloc[0].to_dict(),
            'shap_values': [float(value) for value in shap_values[0]],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Explainability failed: {exc}')
