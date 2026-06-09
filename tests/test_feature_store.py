import importlib
import os
from pathlib import Path

import pandas as pd


def test_local_feature_store(monkeypatch, tmp_path):
    monkeypatch.delenv('HOPSWORKS_PROJECT', raising=False)
    monkeypatch.delenv('HOPSWORKS_API_KEY', raising=False)
    import services.feature_store as fs
    importlib.reload(fs)
    monkeypatch.setattr(fs, 'LOCAL_DB_PATH', str(tmp_path / 'features.db'))

    record = {
        'city': 'TestCity',
        'timestamp': '2026-06-08T00:00:00Z',
        'temp': 25.0,
        'humidity': 50.0,
        'pressure': 1012.0,
        'wind_speed': 2.5,
        'aqi': 3,
        'pm2_5': 12.0,
        'pm10': 20.0,
        'no2': 15.0,
        'o3': 10.0,
        'hour': 12,
        'day': 8,
        'month': 6,
        'aqi_change': 0.5,
    }

    fs.insert_feature(record)
    assert fs.get_last_aqi('TestCity') == 3.0
    df = fs.fetch_features_dataframe()
    assert len(df) == 1
    assert df.iloc[0]['city'] == 'TestCity'
