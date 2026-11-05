"""Fixed-current 24-hour backward baseline; not a full Lagrangian trajectory."""

import numpy as np
import pandas as pd


def constant_current_backtrack(data: pd.DataFrame, hours: int = 24) -> np.ndarray:
    if hours < 1:
        raise ValueError("History horizon must be positive")
    required = {"current_u", "current_v"}
    if not required.issubset(data.columns):
        raise ValueError("Current components required for physical baseline")
    current = data[["current_u", "current_v"]].to_numpy(dtype=float)
    if not np.isfinite(current).all():
        raise ValueError("Current components must be finite m/s values")
    return -current * hours * 3.6
