import numpy as np
import pandas as pd
import pytest

from bluetrace_ml.physics import constant_current_backtrack


def test_eastward_current_predicts_westward_previous_position():
    frame = pd.DataFrame({"current_u": [0.2], "current_v": [0.0]})
    offsets = constant_current_backtrack(frame, hours=24)
    assert offsets.shape == (1, 2)
    np.testing.assert_allclose(offsets[0], [-17.28, 0.0], atol=1e-10)


def test_missing_currents_cannot_be_interpreted_as_zero():
    with pytest.raises(ValueError, match="finite"):
        constant_current_backtrack(pd.DataFrame({
            "current_u": [float("nan")], "current_v": [0.1]
        }))
