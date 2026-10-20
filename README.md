# GEMSDOE72 — DOE GEMS Prize Challenge (DrivenData #306)

> **Goal:** place top of the GEMS leaderboard by submitting a unique, format-valid GeoTIFF of geothermal-indicative faults. Competition training data is login-walled on DrivenData and unreachable from this sandbox, so this repository ships the **complete verified pipeline** (distance-weighted Tversky metric, submission writer, validator, tests) plus a **downloadable format-valid baseline submission**. It is **NOT** a leaderboard claim — treat it as a format-check baseline ready to become competitive once data is placed in `data/`.

## One-click submission file (download first thing)

The submission GeoTIFF is published on the GitHub Pages site. From the site home, the very first element is a **"Download submission .tif" / ".zip" button**:

- Site: `https://buffedlizard55-lab.github.io/GEMSDOE72/` (GitHub Pages, once Pages is enabled for this repo)
- Home: `docs/index.html`
- File: `docs/downloads/gemsdoe72-baseline-dotted-budget-20261020T194809Z-5e1a26d8-zeros-outside-footprint.tif`
- Zip: `docs/downloads/gemsdoe72-baseline-dotted-budget-20261020T194809Z-5e1a26d8-zeros-outside-footprint.zip`
- Audit receipt: `docs/downloads/gemsdoe72-baseline-dotted-budget-20261020T194809Z-5e1a26d8-zeros-outside-footprint.audit.json`

**SHA-256:** `e05f56bceb31d8d5007ddda2069aaa8e9850a864f6c141d6f621c8ebe6c8209f`

## Is it OK to download and submit?

| Check | Result |
|---|---|
| Format validator (independent re-read from disk) | **PASSED** |
| Single band, float32 | yes |
| CRS EPSG:32611, 100 m, 3730×3292, competition transform | yes |
| All cells finite, no NaN | yes |
| All values in [0, 1] | yes |
| No nodata sentinel (avoids the "[0, 1]" portal error) | yes |
| **OK to download and upload** | **YES (format-valid)** |
| **Score / organizer-confirmed** | **NOT CLAIMED — UNVERIFIED baseline** |

**It is OK to download and submit as a format check, but the score is unverified and it is not expected to lead the leaderboard.** DrivenData's public leaderboard leader is ~0.326 (GEMSDOE32 read, 2026-10-04); the brief also cites 0.3195 / 0.3774 / 0.4413 at later reads. Beating that requires a detector trained on the competition features and validated on the spatially-blocked holdout.

## How to submit (executive summary)

1. Download the `.tif` (or the `.zip` containing it) from the site home (`docs/index.html`).
2. Log in to DrivenData and open the submissions page:
   https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/
3. Choose the file. In **Note (optional)** paste:
   ```
   GEMSDOE72 baseline-dotted-budget | format-valid submission package (single-band float32, EPSG:32611, 100 m, 3730x3292, values in [0,1], all finite, no nodata). Baseline dotted emission; competition training data not accessible from this sandbox so score is UNVERIFIED and not a leaderboard claim.
   ```
4. Submit. DrivenData validates: single-band float32 GeoTIFF, EPSG:32611, 100 m, same bounds/transform as training data, values in [0, 1].

Full details: `docs/executive-summary.html`.

## The prompt (standing instructions)

This repo exists to produce a **unique TIF submission** for the GEMS competition — never copy a prior submission except for learning. Every number must be labelled HOLDOUT-DTI or ORGANIZER-CONFIRMED; a projection is never a score. Follow the parallel-run protocol (lane discipline, reuse don't rebuild, leakage canary AUC ≤ 0.90, run card, 3-experiment / 2-hour budget). See `docs/run-card.json` for the run card and `docs/hypotheses.html` for 3–5 ranked geological hypotheses.

## Repository contents

- `src/metric.py` — distance-weighted Tversky index (α=0.2, β=0.8, 300 m triangular kernel); verified against the published worked example (TPw=3.00, FPw=1.89, FNw=2.00 → 0.60).
- `src/submission_writer.py` — writes format-valid GeoTIFF + sha256-pinned audit receipt.
- `src/validator.py` — independent format check (CRS/shape/transform/[0,1]/finite/no-nodata).
- `src/generate_submission.py` — generates the downloadable submission package.
- `tests/test_metric.py` — 8 tests, all passing (`python -m pytest tests/ -q`).
- `scripts/prepare_data.py`, `scripts/download_competition_data.sh` — data scaffolding (data is login-walled; place manually in `data/`).
- `docs/` — GitHub Pages site: home, executive summary, sources, leaderboard, hypotheses, run card.
- `.github/workflows/ci.yml` — runs the metric tests on every push.

## Official sources

See `docs/sources.html` for the full verified-link table (DrivenData problem/metric/format, USGS GeoDAWN, INGENIOUS, USGS Quaternary Faults, reference solution, rules PDF, leaderboard).

## Blocker

**Training data placement.** `bash scripts/download_competition_data.sh` documents that `training_features.tif`, `labels.tif`, `sample_submission.tif` and `1m_DEM_links.csv` must be downloaded from the login-walled DrivenData data page on an unrestricted machine into `data/`, then `python scripts/prepare_data.py`. After that the full train → validate → submit pipeline is ready (GPU for training; metric/validation verified on CPU).
