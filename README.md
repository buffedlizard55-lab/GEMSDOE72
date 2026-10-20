# GEMSDOE72 — auditable GEMS submission research

> **Project brief — read this before every work session.** Build an auditable, useful system for discovering geothermal-relevant faults absent from the USGS/INGENIOUS catalogue and producing a valid, easy-to-download DrivenData submission GeoTIFF. Maximize the probability of a scientifically defensible win; own outcomes, report negative results, and never present a forecast as a score. Use free, official data and cite verifiable sources. Preserve an up-to-date, reviewable evidence feed. The top of the site must state plainly whether a GeoTIFF is safe to download and submit. A submission must have a unique name and a note no longer than the form's limit. Keep an executive summary with exact submission instructions.
>
> **Scientific/competition protocol.** Before experiments, inspect the repository and register 3–5 candidate hypotheses: name the actual layers, physical signature, why the target could be missing from the catalogue, how it differs from code already present, expected benefit, cost, and external-data status. Check that official external data is obtainable before calling an idea viable. Use the shared feature cache, holdout evaluator, and writer rather than private forks when they exist. Holdout means spatially blocked hide-and-recover of whole fault segments with a buffer; derive catalogue-based features only from visible faults; mask visible faults pixel-exactly; score pooled DTI with alpha 0.2, beta 0.8, and the 300 m triangular distance kernel. Test individual features as leakage canaries. Never promote a candidate that has not beaten the current holdout best. Do not use a submission slot as an experiment. Stop at three experiments or two hours. Check candidate rasters against registry rasters before placement and on final dots; if rank correlation exceeds 0.90 or over 70% of dots fall within 3 pixels of a registry raster, flag a duplicate and stop. Label each numeric result as either **HOLDOUT-DTI** (evaluator version, withheld-positive count, 95% CI) or **ORGANIZER-CONFIRMED** (copied from a DrivenData receipt). Projections are not scores. End experiment reports with the agreed JSON run card: hypothesis; mechanism; named non-fault mimic; holdout DTI and CI; registry correlation/overlap; raster SHA-256; format validation (no NaN inside footprint, values in [0,1], CRS/shape/transform match); submission name and <=140-character note; verdict promote/negative.
>
> **Submission-format requirements (official competition specification).** One-band float32 GeoTIFF; EPSG:32611; 100 m; exact training-grid bounds, shape and geotransform; predicted values in [0,1]; outside-footprint values null/NaN. Validate the written bytes by reopening them. Never create or offer a synthetic, copied, or unvalidated raster as a competition candidate. If required private competition data or shared tools are missing, say so prominently and do not fabricate a TIF or score.
>
> **Research and product requirements.** Review the full official problem, about, data, and rules pages; distinguish official facts from team-reported claims and hypotheses; provide links for manual verification; flag contradictions and limitations. Keep useful scientific knowledge organized with provenance. Work in review passes: (1) implement, (2) audit assumptions/edge cases, (3) re-check the request and final output. Core values: **Maximize P(Win)** and **Own the Outcome**—report defects, failures, and negative evidence rather than hiding them.
>
> **Source brief and history supplied by the project owner.** The owner-provided history names numerous GEMSDOE sibling sites and reported scores, including a GEMSDOE32 artifact reported as 0.2778, a historic 0.3195 reference, and a later 0.4413 figure. These are time-dependent and not interchangeable: verify against the official leaderboard, and label sibling-site figures as owner/site-reported unless a DrivenData receipt confirms them. Never infer that a sibling raster is a valid new submission or copy it.

## Status today

**No submission GeoTIFF is included in this checkout. Do not download or submit anything from this repository yet.** The checkout contains only this README at baseline: no `data/`, cached feature stack, registry rasters, `evaluate_holdout.py`, `submission_writer.py`, competition sample raster, or working model pipeline. Consequently we cannot validate geometry, value bounds, uniqueness, correlation/overlap, holdout DTI, confidence intervals, or calculate a raster hash. The competition data page is login-gated, and this environment does not have the DrivenData files. Fabricating zeros or a random raster would neither be a scientific submission nor a safe response to the portal's range error.

The official current public leaderboard was fetched on **2026-10-20**: top public DW-Tversky score **0.4413** (ORGANIZER-CONFIRMED leaderboard listing; not a submission receipt). The previously cited 0.3195 is no longer the top entry on that page. The GEMSDOE32 page reports the named artifact as 0.2778, but the same page says no artifact has an organizer score; therefore treat 0.2778 as **owner/site-reported, not organizer-confirmed**. The official page describes the metric and submission format; its metric is a distance-weighted Tversky index (alpha 0.2, beta 0.8, 300 m support).

## What is in this starter repository

- [`index.html`](index.html): GitHub Pages landing page with an unmistakable download/submission readiness status.
- [`docs/executive-summary.html`](docs/executive-summary.html): step-by-step portal submission instructions and validation checklist.
- [`docs/hypotheses.html`](docs/hypotheses.html) / [`docs/hypotheses.md`](docs/hypotheses.md): ranked, explicitly unvalidated research candidates with data/source status.
- [`docs/review.html`](docs/review.html) / [`docs/review.md`](docs/review.md): repository audit, source checks, contradictions, and next steps.
- [`.github/workflows/pages.yml`](.github/workflows/pages.yml): static GitHub Pages deployment and daily leaderboard snapshot refresh (requires Pages to be enabled for GitHub Actions in repository settings).
- [`scripts/refresh_leaderboard.py`](scripts/refresh_leaderboard.py): fail-closed parser for the public DW-Tversky leaderboard; publishes only listing evidence, never a submission receipt.
- [`tests/`](tests/): dependency-free checks for readiness messaging, local links, unmeasured run-card fields, and leaderboard parsing.

## Run the site locally

No build step is required. Open `index.html` directly, or run `python -m http.server 8000` from the repository root.

## Official references

- [Competition overview and rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Problem, metric, and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [About and additional references](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [Competition data page (login may be required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS regional data compilation, GDR 1391](https://gdr.openei.org/submissions/1391)
- [Official competition rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
