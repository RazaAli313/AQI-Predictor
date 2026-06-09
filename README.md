# AQI-Predictor (minimal server-side implementation)

This repo now contains a minimal end-to-end implementation focused on the server side (FastAPI) to support an AQI prediction pipeline.

What I added:
- `/api/aqi` - fetches current weather and air quality for a city (OpenWeather)
- `/api/features/fetch` - fetch current weather+aqi and store computed features in Hopsworks
- `/api/features/backfill` - placeholder backfill (best-effort; historical pollution data may be unavailable in free APIs)
- `/api/train` - train a RandomForestRegressor on stored features and register it with MLflow
- `/api/predict` - predict AQI using the latest registered model
- `/api/alerts` - check if latest AQI for a city exceeds a threshold and deliver alerts via webhook/email
- `/api/eda` - export simple EDA summaries and correlations from stored feature data
- `/api/explain` - generate SHAP explanations for the latest city prediction

Storage & models:
- By default, features are persisted in a Hopsworks Feature Store using `services/feature_store.py`.
- MLflow is used for model tracking and registry via `services/model_registry.py`.
- A local SQLite fallback is available only for development when Hopsworks configuration is not provided.

New environment variables:
- `HOPSWORKS_PROJECT`
- `HOPSWORKS_API_KEY`
- `HOPSWORKS_HOST` (optional)
- `MLFLOW_TRACKING_URI`
- `MLFLOW_REGISTERED_MODEL_NAME`
- `ALERT_WEBHOOK_URL`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `ALERT_EMAIL_TO`, `ALERT_EMAIL_FROM`

Limitations & notes:
- OpenWeather free tier does not provide historical air pollution data. The `/api/features/backfill` endpoint uses repeated current fetches as a placeholder.
- This implementation is production-ready for Hopsworks feature storage and MLflow model tracking with alert delivery via webhook or email.

Run locally:
1. Create a virtualenv and install deps:
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```
2. Set `OPEN_WEATHER_API_KEY` in environment.
3. Start app:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

4. Run tests:
```bash
pytest -q
```
