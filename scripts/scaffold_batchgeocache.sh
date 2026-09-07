#!/usr/bin/env bash
# scaffold_batchgeocache.sh
#
# Scaffolds the BatchGeoCache repo directory structure + core starter files.
# Run this from the ROOT of your already-cloned, empty BatchGeoCache repo:
#
#   bash scaffold_batchgeocache.sh
#
# Safe to re-run: every write uses a "skip if exists" guard, so it will never
# clobber PROGRESS.md or anything you've already edited by hand.

set -euo pipefail

PKG="batchgeocache"

write_if_absent() {
  # $1 = path, rest = content piped in via stdin
  local path="$1"
  if [ -e "$path" ]; then
    echo "skip (exists): $path"
  else
    cat > "$path"
    echo "created:       $path"
  fi
}

mkdir_p() {
  mkdir -p "$1"
  echo "dir ok:        $1"
}

echo "== Scaffolding BatchGeoCache =="

# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------
mkdir_p "src/${PKG}"
mkdir_p "tests"
mkdir_p "notebooks"
mkdir_p "specs"
mkdir_p ".github/workflows"

# Placeholders so git tracks otherwise-empty dirs
touch "notebooks/.gitkeep" "specs/.gitkeep"

# ---------------------------------------------------------------------------
# src/batchgeocache/  -- empty/starter module stubs
# (Real migration/generalization from the Calgary prototype happens in Step 4;
#  these are placeholders so the package is importable from day one.)
# ---------------------------------------------------------------------------
write_if_absent "src/${PKG}/__init__.py" <<'EOF'
"""BatchGeoCache: city-agnostic batch address geocoding via Nominatim."""

__version__ = "0.1.0"
EOF

for mod in address_normalizer config geocoder helper_functions inspect_results \
           io_utils logging_utils models package_processor result_combiner state_manager; do
  write_if_absent "src/${PKG}/${mod}.py" <<EOF
"""${mod}: TODO migrate/generalize from the Calgary prototype (Step 4)."""
EOF
done

# ---------------------------------------------------------------------------
# tests/
# ---------------------------------------------------------------------------
write_if_absent "tests/__init__.py" <<'EOF'
EOF

write_if_absent "tests/test_placeholder.py" <<'EOF'
"""Placeholder test so CI has something to run before real tests land."""

from batchgeocache import __version__


def test_version_is_set():
    assert __version__
EOF

# ---------------------------------------------------------------------------
# pyproject.toml
# ---------------------------------------------------------------------------
write_if_absent "pyproject.toml" <<'EOF'
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "batchgeocache"
version = "0.1.0"
description = "City-agnostic, resumable batch address geocoding via the Nominatim API."
readme = "README.md"
requires-python = ">=3.9"
license = { text = "MIT" }
dependencies = [
    "geopy>=2.4",
    "pandas>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
EOF

# ---------------------------------------------------------------------------
# README.md
# ---------------------------------------------------------------------------
write_if_absent "README.md" <<'EOF'
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
EOF

# ---------------------------------------------------------------------------
# .gitignore
# ---------------------------------------------------------------------------
write_if_absent ".gitignore" <<'EOF'
# Python
__pycache__/
*.py[cod]
*.egg-info/
build/
dist/

# Virtual environments
.venv/
venv/
env/

# Notebooks
.ipynb_checkpoints/

# Data (client data never belongs in this repo)
data/
*.zip

# OS / editor cruft
.DS_Store
.vscode/
.idea/

# Test / coverage
.pytest_cache/
.coverage
htmlcov/
EOF

# ---------------------------------------------------------------------------
# LICENSE (MIT) -- portfolio-quality public repo
# ---------------------------------------------------------------------------
write_if_absent "LICENSE" <<'EOF'
MIT License

Copyright (c) 2026 <YOUR NAME>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
EOF

# ---------------------------------------------------------------------------
# CI: run tests on push / PR
# ---------------------------------------------------------------------------
write_if_absent ".github/workflows/ci.yml" <<'EOF'
name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install package + dev deps
        run: pip install -e ".[dev]"
      - name: Run tests
        run: pytest
EOF

echo "== Done. Note: PROGRESS.md is intentionally untouched by this script. =="
