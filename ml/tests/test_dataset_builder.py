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


def test_available_years_skips_unavailable_periods(monkeypatch):
    times = pd.to_datetime(["2003-01-01T00:00:00Z", "2011-01-01T00:00:00Z", "2018-01-01T00:00:00Z"], utc=True)
    pairs = pd.DataFrame({"ID": [1, 2, 3], "time": times,
                          "latitude": [36.8] * 3, "longitude": [-122.0] * 3})
    def fake_select(pairs, sample_size, year, days):
        if year == 2003:
            raise ValueError("No eligible window")
        return pairs.loc[pairs["time"].dt.year.eq(year)].copy()
    monkeypatch.setattr(build_dataset, "select_observations", fake_select)
    choices = build_dataset.available_years(pairs)
    assert [item["year"] for item in choices] == [2011, 2018]
    assert build_dataset.resolve_years(pairs, [2011], 24) == [2011]


def test_auto_selection_requires_enough_years():
    import pytest
    available = [{"year": 2001}, {"year": 2011}]
    with pytest.raises(ValueError, match="Only 2 eligible"):
        build_dataset.choose_years(available, count=3)


def test_auto_selection_spreads_years():
    years = [{"year": 2001 + i} for i in range(9)]
    assert build_dataset.choose_years(years, 3) == [2001, 2005, 2009]
