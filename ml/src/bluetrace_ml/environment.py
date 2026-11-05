"""Strict join for externally sampled historical environmental predictors.

Requires one pre-extracted row per NOAA observation, same ID + UTC timestamp.
No imputation, no look-ahead, no interpolation, no drifter-measured velocities.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from .features import ENVIRONMENT_FEATURES


def join_environment(pairs: pd.DataFrame, path: str | Path):
    environment = pd.read_csv(path)
    required = {"ID", "time", "sample_latitude", "sample_longitude", *ENVIRONMENT_FEATURES}
    missing = required - set(environment.columns)
    if missing:
        raise ValueError(f"Missing environment columns: {sorted(missing)}")
    environment["time"] = pd.to_datetime(environment["time"], utc=True, errors="raise")
    if environment.duplicated(["ID", "time"]).any():
        raise ValueError("Duplicate environment ID/time rows")
    fields = ["ID", "time", "sample_latitude", "sample_longitude", *ENVIRONMENT_FEATURES]
    joined = pairs.merge(environment[fields], on=["ID", "time"], how="left",
                         validate="one_to_one", indicator=True)
    distance = np.sqrt((joined["latitude"] - joined["sample_latitude"]) ** 2 +
                       ((joined["longitude"] - joined["sample_longitude"]) *
                        np.cos(np.radians(joined["latitude"]))) ** 2)
    valid = joined["_merge"].eq("both") & distance.le(0.3)
    for variable in ENVIRONMENT_FEATURES:
        valid &= pd.to_numeric(joined[variable], errors="coerce").notna()
    result = joined.loc[valid].drop(columns=["_merge"]).copy()
    if result.empty:
        raise ValueError("No complete environment overlap with NOAA drifter observations")
    if result["ID"].nunique() < 6:
        raise ValueError("Environmental overlap covers fewer than six drifters")
    coverage = {
        "paired_rows_before_join": int(len(pairs)),
        "paired_rows_after_join": int(len(result)),
        "fraction": float(len(result) / len(pairs)),
        "drifters_with_complete_environment": int(result["ID"].nunique()),
    }
    return result.reset_index(drop=True), coverage
