import os
from typing import Optional

import mlflow
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient

DEFAULT_REGISTERED_MODEL_NAME = os.getenv("MLFLOW_REGISTERED_MODEL_NAME", "AQI_Predictor")


def register_model(run_id: str, artifact_path: str = "model") -> dict:
    model_name = DEFAULT_REGISTERED_MODEL_NAME
    model_uri = f"runs:/{run_id}/{artifact_path}"
    client = MlflowClient()
    try:
        result = mlflow.register_model(model_uri, model_name)
        return {
            "registered_model_name": model_name,
            "version": result.version,
            "model_uri": model_uri,
        }
    except MlflowException:
        return {"registered_model_name": model_name, "model_uri": model_uri}


def load_latest_model():
    client = MlflowClient()
    model_name = DEFAULT_REGISTERED_MODEL_NAME
    try:
        versions = client.get_latest_versions(model_name, stages=["Production", "Staging", "None"])
        if not versions:
            return None
        latest = sorted(versions, key=lambda v: int(v.version), reverse=True)[0]
        model_uri = f"models:/{model_name}/{latest.stage}"
        return mlflow.pyfunc.load_model(model_uri)
    except Exception:
        try:
            return mlflow.pyfunc.load_model(f"models:/{model_name}/None")
        except Exception:
            return None
