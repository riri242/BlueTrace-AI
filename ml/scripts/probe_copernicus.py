"""Download a *small* historical California sample for data-availability checks.

Install: pip install -e ".[marine]"
Authenticate with Copernicus Marine Toolbox if prompted.
This is an access/coverage probe, NOT an environment/NOAA training join.
"""
import argparse
import json
from pathlib import Path


PRODUCTS = {
    "currents": {
        "product": "GLOBAL_MULTIYEAR_PHY_001_030",
        "dataset": "cmems_mod_glo_phy_my_0.083deg_P1D-m",
        "variables": ["uo", "vo"],
    },
    "waves": {
        "product": "GLOBAL_MULTIYEAR_WAV_001_032",
        "dataset": "cmems_mod_glo_wav_my_0.2deg_PT3H-i",
        "variables": ["VSDX", "VSDY", "VHM0"],
    },
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2011-03-25")
    parser.add_argument("--end", default="2011-03-27")
    parser.add_argument("--latitude", type=float, default=36.8)
    parser.add_argument("--longitude", type=float, default=-122.0)
    parser.add_argument("--span", type=float, default=0.5)
    parser.add_argument("--output", default="data/raw/probes")
    args = parser.parse_args()
    try:
        import copernicusmarine
        import xarray as xr
    except ImportError as exc:
        raise SystemExit('Install marine extras: pip install -e ".[marine]"') from exc

    target = Path(args.output)
    target.mkdir(parents=True, exist_ok=True)
    for kind, item in PRODUCTS.items():
        filename = f"{kind}_{args.start}_{args.end}.nc"
        kwargs = {
            "dataset_id": item["dataset"],
            "variables": item["variables"],
            "minimum_latitude": args.latitude - args.span,
            "maximum_latitude": args.latitude + args.span,
            "minimum_longitude": args.longitude - args.span,
            "maximum_longitude": args.longitude + args.span,
            "start_datetime": args.start,
            "end_datetime": args.end,
            "output_directory": str(target),
            "output_filename": filename,
            "overwrite_output_data": True,
        }
        if kind == "currents":
            kwargs["minimum_depth"] = 0
            kwargs["maximum_depth"] = 1
        print(json.dumps({"stage": "request", "dataset": item["dataset"], "kind": kind}))
        try:
            copernicusmarine.subset(**kwargs)
            with xr.open_dataset(target / filename) as ds:
                report = {
                    "kind": kind,
                    "dataset": item["dataset"],
                    "dimensions": dict(ds.sizes),
                    "variables": {
                        variable: {
                            "available": variable in ds,
                            "valid_samples": int(ds[variable].count().item()) if variable in ds else 0,
                            "units": ds[variable].attrs.get("units") if variable in ds else None,
                        }
                        for variable in item["variables"]
                    },
                }
                print(json.dumps(report, default=str))
        except Exception as exc:
            print(json.dumps({"kind": kind, "status": "failed", "reason": str(exc)}))
            raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
