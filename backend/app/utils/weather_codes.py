"""
weather_codes.py

Utility functions for converting WMO weather codes returned by
the Open-Meteo Historical Forecast API into human-readable text.

Reference:
https://open-meteo.com/en/docs
"""


from typing import Dict


WMO_WEATHER_CODES: Dict[int, str] = {
    # Clear
    0: "Clear Sky",

    # Mainly Clear / Partly Cloudy / Overcast
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",

    # Fog
    45: "Fog",
    48: "Depositing Rime Fog",

    # Drizzle
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",

    # Freezing Drizzle
    56: "Light Freezing Drizzle",
    57: "Dense Freezing Drizzle",

    # Rain
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",

    # Freezing Rain
    66: "Light Freezing Rain",
    67: "Heavy Freezing Rain",

    # Snow
    71: "Slight Snow Fall",
    73: "Moderate Snow Fall",
    75: "Heavy Snow Fall",

    # Snow Grains
    77: "Snow Grains",

    # Rain Showers
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",

    # Snow Showers
    85: "Slight Snow Showers",
    86: "Heavy Snow Showers",

    # Thunderstorm
    95: "Thunderstorm",

    # Thunderstorm with Hail
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail",
}


def weather_code_to_text(code: int) -> str:
    """
    Convert a WMO weather code into a human-readable description.

    Args:
        code: Integer WMO weather code.

    Returns:
        Weather description string.
    """
    return WMO_WEATHER_CODES.get(code, "Unknown Weather")


def is_precipitation(code: int) -> bool:
    """
    Returns True if the weather code indicates any type of precipitation.
    """
    return code in {
        51, 53, 55,
        56, 57,
        61, 63, 65,
        66, 67,
        71, 73, 75,
        77,
        80, 81, 82,
        85, 86,
        95, 96, 99,
    }


def is_clear(code: int) -> bool:
    """
    Returns True if weather conditions are mostly clear.
    """
    return code in {0, 1}


def is_cloudy(code: int) -> bool:
    """
    Returns True for cloudy or overcast conditions.
    """
    return code in {2, 3}


def is_fog(code: int) -> bool:
    """
    Returns True if fog is present.
    """
    return code in {45, 48}


def is_rain(code: int) -> bool:
    """
    Returns True for rain or drizzle.
    """
    return code in {
        51, 53, 55,
        56, 57,
        61, 63, 65,
        66, 67,
        80, 81, 82,
    }


def is_snow(code: int) -> bool:
    """
    Returns True for snow conditions.
    """
    return code in {
        71, 73, 75,
        77,
        85, 86,
    }


def is_thunderstorm(code: int) -> bool:
    """
    Returns True for thunderstorm conditions.
    """
    return code in {95, 96, 99}