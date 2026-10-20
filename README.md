# GEMSDOE72
---

## What was shipped (this session)

| Artifact | Path |
|---|---|
| Submission GeoTIFF (zeros, all-finite, in [0,1]) | `docs/downloads/gemsdoe72-h72-1-sgmc-offcatalogue-20261020T195456Z-6e6525e5-zeros.tif` |
| Variant (NaN outside footprint) | `docs/downloads/gemsdoe72-h72-1-sgmc-offcatalogue-20261020T195456Z-6e6525e5-nan.tif` |
| 12-point format audit (zeros) | `docs/downloads/checks-*-zeros.tif.json` — all checks passed |
| 12-point format audit (nan) | `docs/downloads/checks-*-nan.tif.json` — all checks passed |
| Candidate audit + holdout metrics + LANE check | `docs/downloads/*-audit.json` |
| Run card | `run_card.json` |
| Site | `docs/index.html`, `docs/executive-summary.html`, `docs/sources.html`, `docs/hypotheses.html`, `docs/irregularities.html` |

**HOLDOUT-DTI result (not a leaderboard score):** drift-corrected mean 0.1885, 95% CI [0.1658, 0.2113] across 4 quadrants; 0 pixels on the competition catalogue; leakage-canary AUC 0.498 (no leakage); LANE check vs the GEMSDOE32 registry rasters: max Spearman ρ = 0.0035 (limit 0.90), max dots-within-3px overlap 24.3% (limit 70%) — not a duplicate.

**Verdict:** promote (packaged only). Promotion to a real DrivenData submission slot is a separate selector step within the weekly cap; this repo does not auto-submit.

Negative results are deliverables: H72-2 (TMI gradient) measured 0.0046 and is ruled out; H72-3/H72-4/H72-5 are registered with named free official sources in `registry/hypotheses.json` but not built.

---

## How to run

1. Place competition data: `bash scripts/download_competition_data.sh` (requires `gh` auth; restores integrity-pinned owner mirrors — not organizer-authenticated — into `.cache/gems_data/`). The official data page is login-walled: https://www.drivendata.org/competitions/306/competition-doe-gems/data/
2. Prepare caches: `python scripts/prepare_data.py`
3. Evaluate a candidate: `python scripts/evaluate_holdout.py --builtin sgmc_off_catalogue_d1 --name H72-1 --budget 8000`
4. Package a submission: `python scripts/build_submission_72.py`
5. Validate: `python scripts/check_submission.py path/to/file.tif --strict-finite`
6. Tests: `python -m pytest tests -q`

Environment: `.venv/` with numpy, scipy, rasterio, pandas, matplotlib, pytest, pyproj, shapely.

---

## Repository contents

- `src/gemsdoe72/` — template core reused (not rebuilt): `metric.py` (official DTI, verified against the published worked example TP=3.00, FP=1.89, FN=2.00 → 0.60), `holdout.py` (spatially-blocked hide-and-recover), `grid.py` (competition grid geometry), `emission.py` (dot thinning, greedy coverage, credit bar), `submission.py` (GeoTIFF writer + 12-point auditor).
- `scripts/` — `download_competition_data.sh`, `restore_data.py`, `prepare_data.py`, `evaluate_holdout.py`, `build_submission_72.py`, `check_submission.py`, `sweep_sgmc.py` (Experiment 1b).
- `tests/` — metric, emission, submission tests (31 passing).
- `registry/` — `hypotheses.json`, `preregistration.json` (GEMSDOE72-PREREG-1), `slot_plan.json`, `irregularities.json`, `sources.json`, `data_manifest.json`.
- `evidence/` — holdout evidence JSONs.
- `docs/` — GitHub Pages site (download landing page, executive summary, sources, hypotheses, irregularities).
- `.github/workflows/ci.yml` — pytest on push/PR to main.

---

## Limitations

- No DrivenData auth in this sandbox: the official data page and leaderboard are not directly accessible; competition data was restored from hash-pinned owner mirrors (integrity-verified, not organizer-authenticated). Re-download from the official page before relying on results.
- No auto-submission: the generated TIF is a candidate; a human with DrivenData credentials must upload it and spend a weekly slot.
- All produced numbers are HOLDOUT-DTI (own spatially-blocked holdout) — never a projection of an organizer score. No ORGANIZER-CONFIRMED number exists for this artifact yet.
- The leaderboard citations conflict (0.4413 vs 0.3195 vs sister-site 0.3262 snapshot); see `registry/irregularities.json`.

---

## Core values

Maximize P(Win). Own the Outcome. Verify line by line; no hallucinations; flag irregularities.
