# BatchGeoCache

A city-agnostic, resumable batch address-geocoding utility built on the
[Nominatim](https://nominatim.org/) API.

## What it does

Given an address dataset (roughly 100–5,000 records), BatchGeoCache:

1. Splits the dataset into packages of up to 100 records each (sized so an
   interrupted run can resume instead of restarting from scratch).
2. Geocodes each package via Nominatim to retrieve address details
   (postal codes in particular).
3. Tracks per-package state/results to support resuming a partial run.
4. Combines all package results into three CSVs — `success`,
   `partial_success`, and `failure` — zipped together for download, with an
   option to purge temporary/local files first.

## Installation

No PyPI package yet — install straight from GitHub:

```bash
pip install git+https://github.com/<org>/BatchGeoCache.git
```

## Usage (Google Colab)

Data in and out is handled with Colab's own upload/download widgets rather
than Google Drive, so no OAuth grant is required:

```python
from google.colab import files
uploaded = files.upload()       # bring in your address CSV
# ... run the pipeline ...
files.download("results.zip")   # get success/partial_success/failure CSVs back
```

All working files live under the Colab VM's local `/content/` path — nothing
is written to Google Drive.

## Project layout

```
src/batchgeocache/   # library code
tests/                # pytest suite
notebooks/            # example/driver notebooks
specs/                # design notes
```

## License

MIT — see [LICENSE](LICENSE).
