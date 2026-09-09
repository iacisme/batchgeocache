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
> **Only Section 4 is your active task.** As you complete each subtask in
> Section 4, tell the user explicitly so they can check it off and update
> this file — don't wait until the end of the session to summarize progress.
> If Section 4's step becomes fully done, say so explicitly so the user can
> compress it into Section 3 and set up Section 4 for the next step.

# BatchGeoCache — Project State
_Last updated: Session 2 (Steps 1–2 complete; Step 3 is the active task)_

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

## 3. Step Log
| # | Step | Status | Summary (fill in only once done — one line) |
|---|------|--------|-----------------------------------------------|
| 1 | Scaffold repo dir structure + core files (bash script, pyproject.toml, README.md, .gitignore) | done | Scaffolded via idempotent `scaffold_batchgeocache.sh`; added pyproject.toml (58 unpinned deps + dev extra), README, .gitignore, MIT LICENSE, GitHub Actions CI, placeholder test — all verified working. |
| 2 | Init Python virtualenv | done | Created via `virtualenvwrapper` (`mkvirtualenv -a $(pwd) -p python3.14`) + `pip install -e ".[dev]"`; update workflow (`-U` / `--upgrade-strategy eager`) confirmed and documented in README. |
| 3 | Confirm `/content` usage in existing prototype (no Drive paths) | in progress | |
| 4 | Migrate/generalize `src/` modules (remove Calgary + Drive assumptions) | not started | |
| 5 | Review migrated files for any remaining Drive coupling | not started | |
| 6 | Build new Colab notebook (git-clone install + mirrored workflow) | not started | |
| 7 | Test/debug notebook end-to-end | not started | |

Status values: `not started` / `in progress` / `blocked` / `done`.
When a step moves to `done`, write its one-line Summary here, then **delete** its detail from
Section 4 — the one-liner is now the only record of it that needs to survive.

## 4. Current Step Detail (full detail — ONLY the active step lives here)
**Step:** #3 — Confirm `/content` usage in existing prototype (no Drive paths)

**Purpose:** This is a diagnostic/audit step only — no code changes yet. It exists to verify,
module by module, that the *existing* Calgary prototype (see Section 1's prototype layout) has
no Google Drive coupling before Step 4 migrates/generalizes it. Confirming this first means
Step 4 can focus purely on de-Calgary-fying the logic, not on hunting for Drive surprises at
the same time.

**Subtasks:**
- [ ] Get the existing prototype's `src/` modules into this session (upload or paste each
      file) — not yet shared, needed to proceed
- [ ] Audit each of the 11 modules (`address_normalizer.py`, `config.py`, `geocoder.py`,
      `helper_functions.py`, `__init__.py`, `inspect_results.py`, `io_utils.py`,
      `logging_utils.py`, `models.py`, `package_processor.py`, `result_combiner.py`,
      `state_manager.py`) for: `/content/drive/...` paths, `google.colab.drive` imports or
      mount calls, or any other Drive-coupled assumption
- [ ] Note (but don't fix yet) any Calgary-specific hardcoding spotted along the way — useful
      context to carry into Step 4
- [ ] Produce a short findings summary: which modules are already Drive-free vs. which need
      changes, to hand off as the starting point for Step 4

**Notes / in-progress findings:**
- (none yet — step just started)

**Blockers:**
- Waiting on the actual prototype source files to be shared in-session; can't audit code that
  hasn't been provided.

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
> **Only Section 4 is your active task.** As you complete each subtask in
> Section 4, tell the user explicitly so they can check it off and update
> this file — don't wait until the end of the session to summarize progress.
> If Section 4's step becomes fully done, say so explicitly so the user can
> compress it into Section 3 and set up Section 4 for the next step.
