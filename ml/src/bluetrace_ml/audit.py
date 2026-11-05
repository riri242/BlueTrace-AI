"""Summarize NOAA drifter data eligibility without training or network access."""

import argparse
import json

from .dataset import make_24h_pairs, read_noaa


def audit(path: str):
    data = read_noaa(path)
    pairs = make_24h_pairs(data)
    return {
        "source_rows": int(len(data)),
        "source_drifters": int(data["ID"].nunique()),
        "first_utc": data["time"].min().isoformat(),
        "last_utc": data["time"].max().isoformat(),
        "eligible_24h_pairs": int(len(pairs)),
        "eligible_drifters": int(pairs["ID"].nunique()),
        "eligible_1993_onward": int((pairs["time"].dt.year >= 1993).sum()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--noaa", required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.noaa), indent=2))


if __name__ == "__main__":
    main()
