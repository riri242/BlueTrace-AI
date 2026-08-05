"""
wind.py

Utility functions for working with wind data.

This module currently provides functionality for converting
wind direction in degrees into a human-readable compass direction.

Example:
    0°   -> N
    45°  -> NE
    90°  -> E
    135° -> SE
    180° -> S
    225° -> SW
    270° -> W
    315° -> NW
"""

from typing import Optional

# 16-point compass rose
COMPASS_DIRECTIONS = [
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
]


def degrees_to_compass(degrees: Optional[float]) -> str:
    """
    Convert wind direction in degrees to a compass direction.

    Args:
        degrees (float | None):
            Wind direction in degrees (0–360).

    Returns:
        str:
            Compass direction (e.g., "N", "SW", "ENE").

    Examples:
        >>> degrees_to_compass(0)
        'N'

        >>> degrees_to_compass(90)
        'E'

        >>> degrees_to_compass(225)
        'SW'

        >>> degrees_to_compass(315)
        'NW'
    """

    if degrees is None:
        return "Unknown"

    # Normalize values outside the range
    degrees = degrees % 360

    # 360° divided into 16 equal sectors (22.5° each)
    index = round(degrees / 22.5) % 16

    return COMPASS_DIRECTIONS[index]


def is_north_wind(degrees: Optional[float]) -> bool:
    """Return True if wind is generally from the north."""
    return degrees_to_compass(degrees) in {"N", "NNE", "NNW"}


def is_east_wind(degrees: Optional[float]) -> bool:
    """Return True if wind is generally from the east."""
    return degrees_to_compass(degrees) in {"E", "ENE", "ESE"}


def is_south_wind(degrees: Optional[float]) -> bool:
    """Return True if wind is generally from the south."""
    return degrees_to_compass(degrees) in {"S", "SSE", "SSW"}


def is_west_wind(degrees: Optional[float]) -> bool:
    """Return True if wind is generally from the west."""
    return degrees_to_compass(degrees) in {"W", "WNW", "WSW"}