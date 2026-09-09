# BatchGeoCache — Project State
_Last updated: Session 3 (Steps 1–4 complete; Step 5 is the active task)_

## 1. Project Charter (static — only edit this to fix an error, never to "refresh" it)
- **Goal:** Generalize a Calgary-specific address-geocoding prototype into BatchGeoCache, a
  city-agnostic batch geocoding utility built on the Nominatim API, delivered as a public
  GitHub repo installable via `git clone` / `pip install git+...` (no PyPI).
- **Why this architecture:** Client is a non-profit with strict privacy requirements; they
  cannot/will not grant Google Drive OAuth access. The only reason Drive was ever used was to
  locate a local `src/` module — so the fix is to stop depending on Drive entirely, not to
  narrow its scope (Drive's OAuth has no narrow-scope option via `google.colab.drive`).
- **What the pipeline does:** Takes address datasets (100–5000 records), splits them into
  packages of up to 100 records each (sized specifically so an interrupted run can resume
  instead of restarting), geocodes each package via the Nominatim API to retrieve address
  details (in particular postal codes), tracks per-package state/results to support that
  resume behavior, then combines all results into three CSVs — `success`, `partial_success`,
  `failure` — zipped for the client to download, with an option to purge temp/local files
  first.
- **Locked-in decisions:**
  - No Google Drive anywhere in the pipeline. `/content/...` local Colab VM paths are fine;
    `/content/drive/...` paths are not.
  - Data in/out with the client uses `google.colab.files.upload()` / `.download()`.
  - Repo name/package name: **BatchGeoCache**. Public repo, doubles as a portfolio piece.
  - This state file lives inside the repo; user (not the AI) commits it after each update.
- **Audience:** Non-profit client deliverable + portfolio showcase.
- **Existing prototype layout to migrate from** (local project root, not yet in the new repo):
  ```
  postal_code_lookups/
  ├── data/                    # NOT going into the repo — local/client data only
  ├── notebooks/
  │   ├── Address_Look_Up.ipynb
  │   ├── CSV_Inspection_Tool.ipynb
  │   └── __superceded__/      # old dev notebooks, not needed going forward
  ├── specs/
  └── src/
      ├── address_normalizer.py
      ├── config.py
      ├── geocoder.py
      ├── helper_functions.py  # LEGACY / UNUSED — excluded from migration (see Decision Log)
      ├── __init__.py
      ├── inspect_results.py
      ├── io_utils.py
      ├── logging_utils.py
      ├── models.py
      ├── package_processor.py
      ├── result_combiner.py
      └── state_manager.py
  ```

## 2. Decision Log (append-only — one line per resolved decision; do not delete old entries)
- Chose to solve the Drive/OAuth privacy problem via a public GitHub repo + `!git clone`
  install, rejecting both "paste everything into one giant notebook" and "publish to PyPI"
  as the primary approach (PyPI was judged more ceremony than needed for a single-client
  utility library).
- Repo/package name chosen: **BatchGeoCache**.
- Package is being generalized to work for any city, not just Calgary.
- Cross-session workflow decided: this PROGRESS.md file lives inside the repo, is
  repo-internal (not external to keep the portfolio repo clean — user preferred internal for
  traceability), and the user commits it manually after each AI-assisted update.
- Repo scaffolded via `scaffold_batchgeocache.sh` — idempotent (safe to re-run, skips
  existing files), confirmed working against a repo containing only `.git` (nothing else).
  Run via `bash scaffold_batchgeocache.sh`; no `chmod +x` needed since it's invoked through
  `bash`, not executed directly.
- `pyproject.toml` dependencies intentionally kept broad and **unpinned** during exploration
  (~58 packages spanning Jupyter, science/geo, mapping, Dash, ML/CV, web scraping, SQL, docs
  tooling). A pinned `production`/`container` extras group is deferred until ready to
  test/validate/deploy — a commented-out skeleton is already left in `pyproject.toml` for
  that point.
- Local dev environment managed via `virtualenvwrapper`, not a bare venv:
  `mkvirtualenv -a $(pwd) -p python3.14 <env>` then `pip install -e ".[dev]"`. Updating all
  packages is `pip install -e ".[dev]" -U` (add `--upgrade-strategy eager` for a fuller
  transitive-dependency refresh). README.md documents this under "Local Development Setup."
- Audited all 11 prototype `src/` modules for Drive coupling: the active pipeline (10
  modules) is entirely Drive-free. Only `helper_functions.py` had Drive coupling
  (hardcoded `/content/drive/...` path, `from google.colab import files`), and nothing in
  `src/` imports it.
- Decided to **drop `helper_functions.py` from the BatchGeoCache migration scope entirely**.
  It predates the current modular architecture (AddressNormalizer / Geocoder /
  PackageProcessor); its logic was already migrated into `geocoder.py` when the user moved
  from a single do-everything function to separate files. It will not be carried into the
  new repo.
- Added a formal Document Format Contract (Section 6) after observing some LLMs tend to
  restructure this file on their own. Retired the duplicate cover instruction that used to
  be pasted above Section 1 — Section 5 + Section 6 together now fully cover that role, so a
  separate top-of-file copy was redundant.
- Chose to store per-boundary geographic sanity-check data (Calgary's, and future
  cities'/provinces' lat/lon bounding box + optional FSA prefixes) in a new `boundaries.toml`
  file rather than a per-boundary field on `GeocoderConfig`, keyed by boundary name and read
  via the stdlib `tomllib` (no new dependency, consistent with `pyproject.toml` already being
  TOML). `inspect_results()` takes a `boundary_name` argument (default `"calgary"`) and skips
  the geographic check gracefully if the named boundary isn't defined yet — only a Calgary
  entry exists for now, by design; more boundaries are a data-file addition, not a code change.
- Step 4 completed: migrated and de-Calgary-fied all 10 in-scope `src/` modules plus
  `__init__.py` into BatchGeoCache's package structure; also removed a dead commented-out
  duplicate block from `config.py` that still referenced the old Calgary `user_agent`.

## 3. Step Log
| # | Step | Status | Summary (fill in only once done — one line) |
|---|------|--------|-----------------------------------------------|
| 1 | Scaffold repo dir structure + core files (bash script, pyproject.toml, README.md, .gitignore) | done | Scaffolded via idempotent `scaffold_batchgeocache.sh`; added pyproject.toml (58 unpinned deps + dev extra), README, .gitignore, MIT LICENSE, GitHub Actions CI, placeholder test — all verified working. |
| 2 | Init Python virtualenv | done | Created via `virtualenvwrapper` (`mkvirtualenv -a $(pwd) -p python3.14`) + `pip install -e ".[dev]"`; update workflow (`-U` / `--upgrade-strategy eager`) confirmed and documented in README. |
| 3 | Confirm `/content` usage in existing prototype (no Drive paths) | done | Audited all 11 modules: the active pipeline (10 modules) is Drive-free. Only legacy/unused `helper_functions.py` had Drive coupling + Calgary hardcoding; it's dropped from migration scope. Calgary hardcoding also noted in `config.py` (user_agent), `address_normalizer.py` (docstring), and `inspect_results.py` (FSA/lat-lon sanity bounds) for Step 4. |
| 4 | Migrate/generalize `src/` modules (remove Calgary + Drive assumptions) | done | Migrated all 10 in-scope modules + `__init__.py`; generalized `config.py` user_agent, `address_normalizer.py` docstring, and `inspect_results.py`'s geographic sanity check (now reads named boundaries from new `boundaries.toml`, Calgary-only entry for now); removed dead Calgary-referencing commented block from `config.py`. |
| 5 | Review migrated files for any remaining Drive coupling | in progress | |
| 6 | Build new Colab notebook (git-clone install + mirrored workflow) | not started | |
| 7 | Test/debug notebook end-to-end | not started | |

Status values: `not started` / `in progress` / `blocked` / `done`.
When a step moves to `done`, write its one-line Summary here, then **delete** its detail from
Section 4 — the one-liner is now the only record of it that needs to survive.

## 4. Current Step Detail (full detail — ONLY the active step lives here)
**Step:** #5 — Review migrated files for any remaining Drive coupling

**Purpose:** Step 3's audit was performed against the *original prototype* files, before
Step 4's migration/generalization edits. This step re-reviews the *migrated* versions —
the 10 in-scope modules, `__init__.py`, and the new `boundaries.toml` — to confirm none of
Step 4's changes introduced any Drive coupling, and that the Step 3 findings still hold true
for the files as they now exist in the BatchGeoCache repo.

**Subtasks:**
- [ ] Review each of the 10 migrated modules + `__init__.py` for Drive-related imports,
      paths, or references (`google.colab.drive`, `/content/drive/...`, Drive OAuth calls)
- [ ] Review the new `boundaries.toml` for the same (not expected, but in scope for
      completeness since it's a new file introduced in Step 4)
- [ ] Cross-check findings against Step 3's original audit for consistency — flag any
      discrepancy rather than silently resolving it
- [ ] Produce a short pass/fail confirmation per module to close out Step 5

**Notes / in-progress findings:**
- (none yet — step just started)

**Blockers:**
- None currently.

## 5. Cover Instruction (paste this ABOVE sections 1–4 when starting a new chat)
> **ACTION REQUIRED — read this before doing anything else.** This file is an
> active work order, not background reading. If you are an AI assistant: your
> task is to read Section 4 (Current Step Detail) and begin working on it
> *immediately, in this response* — do not wait for further prompting, and do
> not just summarize this file back to the user.
>
> You are a senior solutions architect (Python packaging, Bash, Google Colab)
> continuing work on the BatchGeoCache project. Section 1 is fixed
> background — treat it as ground truth, do not restate or re-litigate it.
> Section 2 is a decision history — don't repeat these in your replies, just
> honor them. Section 3 shows overall progress — don't repeat it either.
> Section 6 defines this document's structural contract — follow it exactly. Do not
> restructure, rename, reorder, or reformat any section on your own judgment; if you think the
> structure itself needs to change, propose it to the user instead of changing it.
> **Only Section 4 is your active task.** As you complete each subtask in
> Section 4, tell the user explicitly so they can check it off and update
> this file — don't wait until the end of the session to summarize progress.
> If Section 4's step becomes fully done, say so explicitly so the user can
> compress it into Section 3 and set up Section 4 for the next step.

## 6. Document Format Contract (static — edit only to fix an error in this contract itself)
- This file always has exactly six sections, in this order, with these exact headers:
  `1. Project Charter`, `2. Decision Log`, `3. Step Log`, `4. Current Step Detail`,
  `5. Cover Instruction`, `6. Document Format Contract`. Never rename, reorder, merge, split,
  or add a top-level section without explicit user confirmation first.
- **Section 1** — edit only to correct a factual error. Never rewrite for style or "freshen
  it up." New thinking belongs in Section 2, not here.
- **Section 2** — append-only. Never delete, reorder, or reword an existing bullet. A new
  decision gets exactly one new bullet at the end.
- **Section 3** — the table's header row and column order never change. Permitted edits only:
  update a `Status` value, fill in a `Summary` cell once a step is `done`, or add one new row
  for a newly active step. Never delete or reorder rows, never add/remove columns.
- **Section 4** — the only section fully rewritten each session, but it must always keep this
  internal shape: **Step**, optional **Scope note**, **Purpose**, **Subtasks** (checkbox
  list), **Notes / in-progress findings**, **Blockers**. Don't drop one of these fields or
  invent new ones without flagging it to the user first.
- **Section 5** — verbatim, byte-for-byte, every time. Never edited, shortened, or paraphrased.
- **Section 6 (this section)** — same rule as Section 5: static, edit only to fix an actual
  error in the contract, never to "improve" it.
- **Formatting conventions** — preserve exactly: `- [ ]` checkboxes (not numbered lists),
  the pipe-table format in Section 3, bold field labels in Section 4, fenced code blocks for
  the directory tree, and existing heading levels (`##` for top-level sections). Do not
  reformat any of this on your own judgment.
- If you believe the schema itself genuinely needs to change (a new section, a new table
  column, a different field in Section 4), **do not make the change silently.** State it as a
  proposal to the user in your reply, alongside an otherwise fully compliant, unmodified file —
  never withhold or restructure the file while waiting for the user's decision.
