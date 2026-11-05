This directory contains local and potentially large research datasets.

- raw/: original downloaded sources (ignored by Git)
- interim/: source-specific preprocessing (ignored by Git)
- processed/: aligned training tables (ignored by Git)

Do not commit Copernicus credentials, large NOAA downloads, NetCDF, Parquet,
trained artifacts, or model evaluation files containing per-observation locations.

Use the source manifest in ../configs/data_sources.json to track provenance.
