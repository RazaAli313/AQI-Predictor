from datetime import datetime
from typing import Dict, Any
from .feature_store import get_last_aqi


def compute_features(city: str, weather: Dict[str, Any], air_quality: Dict[str, Any]) -> Dict[str, Any]:
    """Compute features from OpenWeather `weather` and `air_quality` responses."""
    now = datetime.utcnow()
    main = weather.get('main', {})
    wind = weather.get('wind', {})
    aqi_data = None
    components = {}
    try:
        aqi_data = air_quality.get('list', [])[0]
        components = aqi_data.get('components', {})
    except Exception:
        aqi_data = None

    aqi = None
    if aqi_data:
        # OpenWeather maps AQI 1..5
        aqi = aqi_data.get('main', {}).get('aqi')

    last = get_last_aqi(city)
    aqi_change = None
    try:
        if last is not None and aqi is not None:
            aqi_change = float(aqi) - float(last)
    except Exception:
        aqi_change = None

    features = {
        'city': city,
        'timestamp': now.isoformat(),
        'temp': main.get('temp'),
        'humidity': main.get('humidity'),
        'pressure': main.get('pressure'),
        'wind_speed': wind.get('speed'),
        'aqi': aqi,
        'pm2_5': components.get('pm2_5'),
        'pm10': components.get('pm10'),
        'no2': components.get('no2'),
        'o3': components.get('o3'),
        'hour': now.hour,
        'day': now.day,
        'month': now.month,
        'aqi_change': aqi_change,
    }
    return features
