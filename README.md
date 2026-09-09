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
pip install git+https://github.com/iacisme/BatchGeoCache.git
```

## Local Development Setup

Dependencies live in `pyproject.toml`, not a `requirements.txt` — the
commands below use `virtualenvwrapper`'s `mkvirtualenv`, adapted for that.

### Create the environment

```bash
mkvirtualenv -a $(pwd) -p python3.14 BatchGeoCache
```

No `-r requirements.txt` flag — there isn't one. `mkvirtualenv` auto-activates
the new env; to come back to it later, `workon BatchGeoCache` re-activates it
and `cd`s to the project root (that's what `-a $(pwd)` wires up).

### Install the project

From the repo root, with the env active:

```bash
pip install -e ".[dev]"
```

- `-e` (editable) means changes to `src/batchgeocache/*.py` take effect
  immediately, no reinstall needed.
- `[dev]` pulls in `pytest` alongside the full exploratory dependency list.

Verify it worked:

```bash
python -c "import batchgeocache; print(batchgeocache.__version__)"   # -> 0.1.0
pytest                                                                 # placeholder test should pass
```

### Update all dependencies

Everything in `pyproject.toml` is intentionally unpinned during this
exploratory phase, so refreshing is just re-running the install with `-U`:

```bash
pip install -e ".[dev]" -U
```

By default pip only upgrades a package (and its sub-dependencies) if the
currently installed version no longer satisfies the requirement
(`--upgrade-strategy only-if-needed`). For a fuller refresh that also pushes
transitive dependencies forward whenever a newer compatible version exists:

```bash
pip install -e ".[dev]" -U --upgrade-strategy eager
```

`eager` re-resolves the whole dependency tree, so it's slower — but it's the
closer match to "update everything to latest."

### (Optional) snapshot a requirements.txt

If some other tool in the workflow still wants a `requirements.txt` (e.g. a
Colab cell, a Docker build), generate one from the live env rather than
hand-editing it:

```bash
pip freeze > requirements.txt
```

Once a pinned `production` extra is added to `pyproject.toml` for
release/deploy, that becomes the better source of truth instead.

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
