# BatchGeoCache — Project State
_Last updated: Session 1 (repo scaffolding not yet started)_

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
      ├── helper_functions.py
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

## 3. Step Log
| # | Step | Status | Summary (fill in only once done — one line) |
|---|------|--------|-----------------------------------------------|
| 1 | Scaffold repo dir structure + core files (bash script, pyproject.toml, README.md, .gitignore) | in progress | |
| 2 | Init Python virtualenv | not started | |
| 3 | Confirm `/content` usage in existing prototype (no Drive paths) | not started | |
| 4 | Migrate/generalize `src/` modules (remove Calgary + Drive assumptions) | not started | |
| 5 | Review migrated files for any remaining Drive coupling | not started | |
| 6 | Build new Colab notebook (git-clone install + mirrored workflow) | not started | |
| 7 | Test/debug notebook end-to-end | not started | |

Status values: `not started` / `in progress` / `blocked` / `done`.
When a step moves to `done`, write its one-line Summary here, then **delete** its detail from
Section 4 — the one-liner is now the only record of it that needs to survive.

## 4. Current Step Detail (full detail — ONLY the active step lives here)
**Step:** #1 — Scaffold repo directory structure + core files

**Subtasks:**
- [ ] Design the target directory layout for the BatchGeoCache package repo
- [ ] Write a Bash script that scaffolds that layout (dirs + empty/starter files)
- [ ] Draft `pyproject.toml` (installable via `pip install git+https://github.com/<org>/BatchGeoCache.git`)
- [ ] Draft `README.md` reflecting the city-agnostic, Nominatim-based, resumable-batch
      description above
- [ ] Draft `.gitignore`
- [ ] Decide on and add any other recommended files (LICENSE, `tests/` scaffold, CI config,
      etc. — architect's judgment on appropriate scope for a portfolio-quality repo)

**Notes / in-progress findings:**
- Repo has already been created and cloned locally (empty) by the user — ready for scaffolding.
- Nothing in `src/` should reference Drive paths going forward — only local Colab VM paths
  under `/content/`; this will be formally verified in Step 3, not assumed during Step 1.

**Blockers:**
- None currently.

## 5. Cover Instruction (paste this ABOVE sections 1–4 when starting a new chat)
> You are a senior solutions architect (Python packaging, Bash, Google Colab) continuing work
> on the BatchGeoCache project. Section 1 is fixed background — treat it as ground truth, do
> not restate or re-litigate it. Section 2 is a decision history — don't repeat these in your
> replies, just honor them. Section 3 shows overall progress. **Only Section 4 is your active
> task.** As you complete each subtask in Section 4, tell me so I can check it off and update
> this file — don't wait until the end of the session to summarize progress. If Section 4's
> step becomes fully done, tell me explicitly so I can compress it into Section 3 and set up
> Section 4 for the next step.
