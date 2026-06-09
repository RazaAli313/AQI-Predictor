import os
from typing import Dict, Any, Optional

import pandas as pd

USE_HOPSWORKS = bool(os.getenv("HOPSWORKS_PROJECT") and os.getenv("HOPSWORKS_API_KEY"))
HOPSWORKS_FEATURE_GROUP_NAME = "aqi_features"
HOPSWORKS_FEATURE_GROUP_VERSION = 1
LOCAL_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'features.db')

if USE_HOPSWORKS:
    import hopsworks
else:
    import sqlite3


def _hopsworks_project():
    host = os.getenv("HOPSWORKS_HOST")
    project = os.getenv("HOPSWORKS_PROJECT")
    api_key = os.getenv("HOPSWORKS_API_KEY")
    if not project or not api_key:
        raise RuntimeError("Hopsworks configuration is missing.")
    if host:
        return hopsworks.login(host=host, project=project, api_key_value=api_key)
    return hopsworks.login(project=project, api_key_value=api_key)


def _get_feature_store():
    project = _hopsworks_project()
    return project.get_feature_store()


def _get_feature_group():
    fs = _get_feature_store()
    try:
        return fs.get_feature_group(name=HOPSWORKS_FEATURE_GROUP_NAME, version=HOPSWORKS_FEATURE_GROUP_VERSION)
    except Exception:
        schema = [
            "city",
            "timestamp",
            "temp",
            "humidity",
            "pressure",
            "wind_speed",
            "aqi",
            "pm2_5",
            "pm10",
            "no2",
            "o3",
            "hour",
            "day",
            "month",
            "aqi_change",
        ]
        empty_df = pd.DataFrame(columns=schema)
        return fs.create_feature_group(
            name=HOPSWORKS_FEATURE_GROUP_NAME,
            version=HOPSWORKS_FEATURE_GROUP_VERSION,
            description="AQI feature group for prediction pipeline",
            primary_key=["city", "timestamp"],
            online_enabled=True,
            df=empty_df,
        )


def _local_conn():
    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_local_db():
    conn = _local_conn()
    cur = conn.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            timestamp TEXT,
            temp REAL,
            humidity REAL,
            pressure REAL,
            wind_speed REAL,
            aqi INTEGER,
            pm2_5 REAL,
            pm10 REAL,
            no2 REAL,
            o3 REAL,
            hour INTEGER,
            day INTEGER,
            month INTEGER,
            aqi_change REAL
        )
        '''
    )
    conn.commit()
    conn.close()


def insert_feature(record: Dict[str, Any]):
    if USE_HOPSWORKS:
        fg = _get_feature_group()
        df = pd.DataFrame([record])
        fg.insert(df, write_options={"wait_for_job": False})
        return

    _init_local_db()
    conn = _local_conn()
    cur = conn.cursor()
    cur.execute(
        '''
        INSERT INTO features (city, timestamp, temp, humidity, pressure, wind_speed, aqi, pm2_5, pm10, no2, o3, hour, day, month, aqi_change)
        VALUES (:city, :timestamp, :temp, :humidity, :pressure, :wind_speed, :aqi, :pm2_5, :pm10, :no2, :o3, :hour, :day, :month, :aqi_change)
        ''',
        record,
    )
    conn.commit()
    conn.close()


def get_last_aqi(city: str) -> Optional[float]:
    if USE_HOPSWORKS:
        fg = _get_feature_group()
        df = fg.read()
        if df.empty:
            return None
        city_df = df[df["city"] == city].sort_values("timestamp", ascending=False)
        if city_df.empty:
            return None
        return float(city_df.iloc[0]["aqi"])

    _init_local_db()
    conn = _local_conn()
    cur = conn.cursor()
    cur.execute('SELECT aqi FROM features WHERE city = ? ORDER BY id DESC LIMIT 1', (city,))
    row = cur.fetchone()
    conn.close()
    return float(row["aqi"]) if row else None


def fetch_features_dataframe() -> pd.DataFrame:
    if USE_HOPSWORKS:
        fg = _get_feature_group()
        return fg.read()

    _init_local_db()
    conn = _local_conn()
    df = pd.read_sql_query('SELECT * FROM features', conn)
    conn.close()
    return df
