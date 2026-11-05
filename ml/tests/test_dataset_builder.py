"""Offline checks for the multi-year dataset builder's cache and output contract."""
import json

import pandas as pd

from scripts import build_dataset


def frame():
    return pd.DataFrame({
        "ID": [1001, 1002],
        "time": pd.to_datetime(["2011-01-22T00:00:00Z", "2011-01-22T01:00:00Z"], utc=True),
        "latitude": [36.8, 36.9],
        "longitude": [-122.0, -122.1],
    })


def test_selection_fingerprint_is_stable_and_changes_with_location():
    sample = frame()
    assert build_dataset.fingerprint(sample) == build_dataset.fingerprint(sample.copy())
    updated = sample.copy()
    updated.loc[0, "latitude"] += 0.1
    assert build_dataset.fingerprint(updated) != build_dataset.fingerprint(sample)


def test_completed_cache_requires_matching_fingerprint(monkeypatch, tmp_path):
    sample = frame()
    output = tmp_path / "batch"
    output.mkdir()
    sample.to_csv(output / "environment.csv", index=False)
    (output / "manifest.json").write_text(json.dumps({
        "selection_sha256": build_dataset.fingerprint(sample),
        "state": "complete",
    }), encoding="utf-8")
    def reject_network(*args, **kwargs):
        raise AssertionError("Network should not be called when cache is valid")
    monkeypatch.setattr(build_dataset, "subset_marine", reject_network)
    reused, manifest = build_dataset.run_batch(sample, output)
    assert len(reused) == 2
    assert manifest["state"] == "complete"
