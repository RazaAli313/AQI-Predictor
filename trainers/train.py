import os
from datetime import datetime

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from services.feature_store import fetch_features_dataframe
from services.model_registry import register_model

MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "AQI_Predictor")


def train_and_register_model():
    df = fetch_features_dataframe()
    if df.empty:
        raise RuntimeError('No features available for training')

    df = df.dropna(subset=['aqi'])
    features = ['temp', 'humidity', 'pressure', 'wind_speed', 'pm2_5', 'pm10', 'no2', 'o3', 'hour', 'day', 'month']
    for col in features:
        if col not in df.columns:
            df[col] = 0

    X = df[features].fillna(0)
    y = df['aqi'].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)
    mse = mean_squared_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    with mlflow.start_run(run_name="aqi_training") as run:
        mlflow.log_param("model_type", "RandomForestRegressor")
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("mse", mse)
        mlflow.log_metric("r2", r2)
        mlflow.sklearn.log_model(model, artifact_path="model")
        registry_result = None
        if os.getenv("MLFLOW_REGISTERED_MODEL_NAME"):
            registry_result = register_model(run.info.run_id)

    result = {
        'metrics': {'mae': mae, 'mse': mse, 'r2': r2},
        'run_id': run.info.run_id,
        'registered_model': registry_result,
    }
    return result


def load_latest_model():
    from services.model_registry import load_latest_model as load_model

    model = load_model()
    if model is not None:
        return model
    return None
