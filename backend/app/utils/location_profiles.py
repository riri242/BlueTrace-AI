"""
BlueTrace AI
Location Knowledge Base

This file contains handcrafted environmental profiles for each
possible BlueTrace origin.

Milestone 5 uses these values as a rule-based knowledge base.

Later versions can replace these values with:
- Machine Learning
- Fine-tuned models
- Real datasets
"""

from typing import Dict


LOCATION_PROFILES: Dict[str, dict] = {

    # ==========================================================
    # Sandy Beach
    # ==========================================================

    "Sandy Beach": {

        "description":
            "Open coastline dominated by sand with little vegetation.",

        "expected_objects": [
            "person",
            "umbrella",
            "surfboard",
            "chair",
            "boat",
            "bird",
            "kite",
            "dog",
        ],

        "preferred_weather": [
            "Clear sky",
            "Mainly clear",
            "Partly cloudy",
            "Overcast",
        ],

        "temperature": (12, 35),

        "wind_speed": (0, 40),

        "precipitation": (0, 5),

        "priority": 1.0,
    },

    # ==========================================================
    # Rocky Shore
    # ==========================================================

    "Rocky Shore": {

        "description":
            "Rock formations with limited sand and stronger wave action.",

        "expected_objects": [
            "bird",
            "boat",
            "person",
        ],

        "preferred_weather": [
            "Clear sky",
            "Partly cloudy",
            "Overcast",
        ],

        "temperature": (8, 30),

        "wind_speed": (5, 60),

        "precipitation": (0, 10),

        "priority": 1.0,
    },

    # ==========================================================
    # Harbor
    # ==========================================================

    "Harbor": {

        "description":
            "Human-made coastal harbor with docks and vessels.",

        "expected_objects": [
            "boat",
            "truck",
            "car",
            "person",
            "bench",
        ],

        "preferred_weather": [
            "Clear sky",
            "Partly cloudy",
            "Overcast",
        ],

        "temperature": (5, 35),

        "wind_speed": (0, 35),

        "precipitation": (0, 10),

        "priority": 1.2,
    },

    # ==========================================================
    # Wetland
    # ==========================================================

    "Wetland": {

        "description":
            "Coastal marshland rich in birds and vegetation.",

        "expected_objects": [
            "bird",
            "person",
        ],

        "preferred_weather": [
            "Clear sky",
            "Mainly clear",
            "Partly cloudy",
            "Fog",
        ],

        "temperature": (5, 30),

        "wind_speed": (0, 25),

        "precipitation": (0, 15),

        "priority": 1.1,
    },

    # ==========================================================
    # Urban Coast
    # ==========================================================

    "Urban Coast": {

        "description":
            "Beach adjacent to roads, buildings, and urban activity.",

        "expected_objects": [
            "car",
            "truck",
            "bus",
            "person",
            "bicycle",
            "bench",
            "boat",
        ],

        "preferred_weather": [
            "Clear sky",
            "Partly cloudy",
            "Overcast",
        ],

        "temperature": (5, 40),

        "wind_speed": (0, 40),

        "precipitation": (0, 10),

        "priority": 1.0,
    },

    # ==========================================================
    # Cliff Coast
    # ==========================================================

    "Cliff Coast": {

        "description":
            "High coastal cliffs with limited human activity.",

        "expected_objects": [
            "bird",
            "person",
        ],

        "preferred_weather": [
            "Clear sky",
            "Partly cloudy",
            "Overcast",
        ],

        "temperature": (5, 30),

        "wind_speed": (10, 70),

        "precipitation": (0, 10),

        "priority": 1.2,
    },

    # ==========================================================
    # Unknown
    # ==========================================================

    "Unknown": {

        "description":
            "No confident environmental match.",

        "expected_objects": [],

        "preferred_weather": [],

        "temperature": (-100, 100),

        "wind_speed": (0, 200),

        "precipitation": (0, 500),

        "priority": 0.0,
    },
}