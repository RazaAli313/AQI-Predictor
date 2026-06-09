from fastapi.testclient import TestClient
import routers.predict as predict


def test_alerts_route(client: TestClient, monkeypatch):
    monkeypatch.setattr(predict, 'get_last_aqi', lambda city: 5.0)
    monkeypatch.setattr(predict, 'send_alert_notification', lambda city, aqi, threshold: None)

    response = client.get('/api/alerts?city=TestCity&threshold=4')
    assert response.status_code == 200
    assert response.json()['alert'] is True
    assert response.json()['aqi'] == 5.0


def test_eda_route(client: TestClient, monkeypatch):
    import pandas as pd
    data = pd.DataFrame({
        'city': ['TestCity'],
        'timestamp': ['2026-06-08T00:00:00Z'],
        'temp': [20.0],
        'humidity': [50.0],
        'pressure': [1010.0],
        'wind_speed': [3.0],
        'aqi': [2.0],
        'pm2_5': [12.0],
        'pm10': [20.0],
        'no2': [15.0],
        'o3': [10.0],
        'hour': [12],
        'day': [8],
        'month': [6],
        'aqi_change': [0.0],
    })
    monkeypatch.setattr(predict, 'fetch_features_dataframe', lambda: data)
    response = client.get('/api/eda')
    assert response.status_code == 200
    assert response.json()['samples'] == 1
