"""Probe historical Open-Meteo weather and marine variables against NOAA drifter years.

Run from backend: .\\.venv\\Scripts\\python.exe scripts/check_open_meteo_overlap.py
Only checks a few dates/locations; it does not establish full spatiotemporal coverage.
"""
import asyncio
import json

import httpx

SAMPLES = (
    ("1992-06-15", 36.8, -122.0),
    ("2011-03-25", 36.8, -122.0),
    ("2022-06-15", 36.8, -122.0),
    ("2022-10-15", 36.8, -122.0),
    ("2022-10-15", 34.0, -120.0),
    ("2022-10-15", 40.5, -124.5),
)
SOURCES = (
    ("historical_weather_era5", "https://archive-api.open-meteo.com/v1/archive",
     "wind_speed_10m,wind_direction_10m", {"models": "era5"}),
    ("historical_marine_era5_ocean", "https://marine-api.open-meteo.com/v1/marine",
     "ocean_current_velocity,ocean_current_direction,wave_height",
     {"models": "era5_ocean", "cell_selection": "sea"}),
)


async def main():
    async with httpx.AsyncClient(timeout=45) as client:
        for date, latitude, longitude in SAMPLES:
            for name, url, variables, extras in SOURCES:
                params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "start_date": date,
                    "end_date": date,
                    "hourly": variables,
                    "timezone": "GMT",
                    **extras,
                }
                result = {"source": name, "date": date,
                          "latitude": latitude, "longitude": longitude}
                try:
                    response = await client.get(url, params=params)
                    result["http_status"] = response.status_code
                    data = response.json()
                    result["api_error"] = data.get("reason") if isinstance(data, dict) and data.get("error") else None
                    hourly = data.get("hourly", {}) if isinstance(data, dict) else {}
                    if not isinstance(hourly, dict):
                        hourly = {}
                    result["non_null_hourly_values"] = {
                        variable: sum(value is not None for value in hourly.get(variable, []))
                        for variable in variables.split(",")
                    }
                    result["returned_grid"] = {
                        "latitude": data.get("latitude"), "longitude": data.get("longitude")
                    } if isinstance(data, dict) else None
                except (httpx.RequestError, ValueError) as exc:
                    result["request_error"] = str(exc)
                print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
