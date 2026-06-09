import asyncio
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import requests
from fastapi import APIRouter, HTTPException, Query, status


openweather_router = APIRouter(tags=["openweather"])

OPENWEATHER_CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_AIR_POLLUTION_URL = "https://api.openweathermap.org/data/2.5/air_pollution"


def _fetch_weather(city: str, api_key: str) -> dict:
    query_string = urlencode({"q": city, "appid": api_key, "units": "metric"})
    request = Request(
        f"{OPENWEATHER_CURRENT_WEATHER_URL}?{query_string}",
        headers={"Accept": "application/json"},
    )

    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw_body)
        except json.JSONDecodeError:
            detail = raw_body or exc.reason
        raise HTTPException(status_code=exc.code, detail=detail) from exc
    except URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc.reason),
        ) from exc


@openweather_router.get("/weather")
async def get_weather(city: str = Query(..., min_length=1)):
    api_key = os.getenv("OPEN_WEATHER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPEN_WEATHER_API_KEY is not configured",
        )

    return await asyncio.to_thread(_fetch_weather, city, api_key)


def _fetch_air_quality(lat: float, lon: float, api_key: str) -> dict:
    params = {"lat": lat, "lon": lon, "appid": api_key}
    try:
        resp = requests.get(OPENWEATHER_AIR_POLLUTION_URL, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as exc:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text or str(exc)
        raise HTTPException(status_code=resp.status_code, detail=detail) from exc
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@openweather_router.get("/aqi")
async def get_aqi(city: str = Query(..., min_length=1)):
    """Fetch current weather and air quality for a city using OpenWeather APIs."""
    api_key = os.getenv("OPEN_WEATHER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPEN_WEATHER_API_KEY is not configured",
        )

    weather = await asyncio.to_thread(_fetch_weather, city, api_key)
    coord = weather.get("coord") or {}
    lat = coord.get("lat")
    lon = coord.get("lon")
    if lat is None or lon is None:
        raise HTTPException(status_code=500, detail="Could not determine coordinates for city")

    aqi = await asyncio.to_thread(_fetch_air_quality, lat, lon, api_key)
    return {"city": city, "weather": weather, "air_quality": aqi}