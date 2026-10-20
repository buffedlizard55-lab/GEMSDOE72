# GEMSDOE72

GEMS Prize Challenge (DrivenData #306) — candidate submission system for the
DOE Geologic Enhanced Mapping System (GEMS) Prize. Produces a format-validated,
downloadable single-band GeoTIFF submission for the geothermal-fault
prediction competition, plus a clean GitHub Pages site with an executive
summary, official sources, method/run card, and one-click download.

> **Working branch:** `arena/121cb545-gemsdoe72` (do not rename; PR target is
> `main`). Weekly DrivenData submission slots are a separate selector step;
> no slot was spent in this session.

---

## FULL PROMPT (archived — read this first at the start of every work session)

The following is the project prompt. It is stored here verbatim (duplicated
recitals condensed once) so every session starts from the same base.

### Objective

Generate a UNIQUE TIF submission for the competition. Do not copy a previous
submission unless for learning/education. A unique TIF submission must be
generated. It must be obvious whether it is OK to download and submit the
generated TIF submission. There must be an easy-to-download submission TIF
file as described by the prompt. Read the entire prompt.

### Parallel-run protocol

1. LANE — stay inside the single method paragraph for your lane. If your
   raster's rank-correlation with any registry raster exceeds 0.90, or more
   than 70% of your dots fall within 3 px of one registry raster's dots, you
   have drifted into another lane: log it as a duplicate and stop. Check on
   the surface before placement AND on the final dots.
2. REUSE, DON'T REBUILD — use the template's cached feature stack,
   evaluate_holdout.py and submission_writer.py. Holdout = hide-and-recover:
   withhold whole fault segments with a buffer, derive every catalogue-based
   feature only from the visible faults, mask visible faults pixel-exactly,
   score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a
   shared tool is wrong, fix it once in the template and report it; never
   keep a private fork.
3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld
   positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page
   receipt). A projection is never written as a score.
4. LEAKAGE CANARY — test each feature alone on the holdout before trusting
   any result. AUC above 0.90 means leakage until proven otherwise.
5. RUN CARD — end with one JSON card: hypothesis; mechanism; the named
   non-fault process that could mimic it; holdout DTI + CI;
   correlation/overlap vs registry; raster sha256; validator output (no NaN
   inside the footprint, values in [0,1], CRS/shape/transform match);
   submission name + note of at most 140 characters; verdict promote /
   negative. Negative results are deliverables.
6. BUDGET — stop after 3 experiments or 2 hours. Do not pick submissions;
   promotion to a real slot is a separate selector step, within the weekly
   cap shown on the submission page.

### Competition facts (verified from official sources)

- Competition: Geologic Enhanced Mapping System (GEMS) Prize Challenge,
  DrivenData #306, sponsored by DOE Office of Geothermal with NLR.
  https://www.drivendata.org/competitions/306/competition-doe-gems/
- End date: Dec 3, 2026, 11:59 p.m. UTC. Prize pool $300,000 (initial round
  $50,000 top 5 / $10k each; final round $250,000).
- Task: develop models/algorithms predicting geological faults indicative of
  geothermal resources. Ground truth: USGS quaternary faults + INGENIOUS
  (public, known-incomplete); test set = newly identified faults NOT in the
  USGS database, manually labeled by experts (GeoDAWN region).
- Two rounds: Initial (private expert-labeled test set) and Final (expanded
  label set after expert review of all submissions). Same submission scored
  twice; choose one submission before the deadline.
- Metric: distance-weighted Tversky index, alpha = 0.2 (FP penalty),
  beta = 0.8 (FN penalty), triangular kernel R = 300 m (3 px at 100 m),
  epsilon regulariser. DTI = TP_w / (TP_w + 0.2 FP_w + 0.8 FN_w + eps).
  https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Submission format: single-band GeoTIFF, EPSG 32611 (UTM 11N), 100 m,
  same bounds as training data, null/nan outside bounds, float32, values
  in [0, 1]. Sample submission (total fault absence) on the data page.
- External data encouraged, must be shareable with organizers.
- Data (LOGIN REQUIRED): training_features.tif, labels.tif,
  sample_submission.tif, existing_faults.tif, 1m_DEM_links.csv.
  https://www.drivendata.org/competitions/306/competition-doe-gems/data/
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and (DOI 10.5066/P93LGLVQ; ScienceBase 657e1d85d34e23d3533209f7; bbox approx -120.0024/-116.1415, 37.3641/40.7247)
- INGENIOUS: https://gbcge.org/current-projects/ingenious/ ; GDR submission 1391 (DOI 10.15121/1881483)
- EPSG:32611: https://epsg.io/32611 ; Tversky: https://en.wikipedia.org/wiki/Tversky_index
- Rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf

### Prior results context (from GEMSDOE sites)

Highest single GEMSDOE32 entry: h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros
= 0.2778. Current competition leaderboard high cited: 0.4413 / 0.3774 /
0.3195 at different reads (inconsistent across reads; treat all as
unverified-by-us). Pattern among top entries: sparse "dots" (e.g. 37,654–
44,090 px) near but not on catalogue traces, credit-per-dot break-even
approx 0.2 x DTI. GEMSDOE32 pins the competition grid as 3730 x 3292,
EPSG:32611, 100 m, transform [100, 0, 243350, 0, -100, 4508550], all finite,
values in [0,1], no nodata tag (verified via its public audit.json).

### Known submission-form error

DrivenData returns "Predicted values must be in range [0, 1]" both when
values fall outside [0, 1] AND when a -3.4e38 float32 nodata sentinel is
written through. Fix: all-finite raster, nodata=None, clip to [0, 1].

### Site requirements

- GitHub Page with clean, user-friendly UI; official verified links as
  sources; organized, easy-to-read.
- One obvious downloadable submission TIF (download button on the home
  page); state clearly whether it is OK to download and submit.
- Executive summary subpage explaining exactly how to submit.
- Unique submission name + short note (<= 140 chars) for the submit form.

### Core values

Maximize P(Win); Own the Outcome.

### Deliverables in this repo

- scripts/download_competition_data.sh — data placement (manual; login-walled)
- scripts/prepare_data.py — data placement verification
- scripts/evaluate_holdout.py — exact DTI + spatially-blocked segment holdout
- scripts/submission_writer.py — format-valid GeoTIFF writer + audit receipt
- scripts/generate_submission.py — unique candidate generator (3 experiment arms)
- scripts/tests/test_metric.py — metric unit tests (worked-example verified)
- docs/downloads/*.tif, -audit.json, -checks.json — downloadable submission
- docs/index.html — home + one-click download + "OK to submit?" status
- docs/executive-summary.html — how to submit
- docs/method.html — lane, metric, holdout, run card
- docs/sources.html — official verified links
- run_card.json — full run card (JSON)
- README.md — this file (full prompt)

### Data blocker

training_features.tif / labels.tif / sample_submission.tif / existing_faults.tif /
1m_DEM_links.csv require DrivenData login; not accessible from this sandbox.
Run `bash scripts/download_competition_data.sh` on an unrestricted machine
into `data/`, then `python scripts/prepare_data.py`, before training or
holdout evaluation.

---

## What was produced (this session)

Three experiment arms were generated, all format-validated
(`all_checks_passed: true`; single band, float32, EPSG:32611, 3730 x 3292,
transform [100, 0, 243350, 0, -100, 4508550], all finite, values in [0, 1],
no nodata tag):

| experiment | dots | sha256 (prefix) | verdict |
|---|---|---|---|
| control | 13,995 | 83c33e9b… | negative (lower bound) |
| walkerlane | 5,358 | 2bddb233… | negative |
| walkerlane+geothermal (primary) | 8,477 | e75b5616… | negative — format-validated candidate |

Primary download:
`docs/downloads/GEMSDOE72-h71-walkerlane+geothermal-20261020T194646Z-0172d3a9-candidate.tif`
sha256 `e75b56167895808b47c5fd078ad7a8fd4f6e9a8075b60f011260b265952558a7`

Submission name: `GEMSDOE72-H71-WALKERLANE+GEOTHERMAL`
Note (<=140 chars): "GEMSDOE72 H71 WALKERLANE+GEOTHERMAL | Walker Lane
structural-grain dots + geothermal-field clusters; 8477 dots, off-catalogue
by construction; format-valid candidate, organizer score pending"

**OK to download:** yes — format-validated, all values in [0,1].
**OK to submit as a scored entry:** not yet — holdout DTI not measurable
(labels.tif login-walled), no organizer score exists; regrid against the
official sample_submission.tif before any real submission. Overall run-card
verdict: **negative** (negative results are deliverables).

### Hypothesis (lane)

Undiscovered geothermal-indicative faults concentrate along the Walker Lane
structural grain and at known geothermal fields, where youthful/concealed
traces are missing from the USGS/INGENIOUS catalogue. Named non-fault
mimicking process: distributed background strain / microseismicity (and
paleo-geothermal sinter systems) can localize fluid flow without discrete
mappable faults.

## How to run

```bash
# 1. (External machine, logged into DrivenData) download competition data into data/
bash scripts/download_competition_data.sh   # documents the manual step
# 2. Verify placement
python scripts/prepare_data.py
# 3. Metric tests
python -m scripts.tests.test_metric
# 4. Generate a candidate
python scripts/generate_submission.py --exp walkerlane+geothermal
# 5. Evaluate (needs labels.tif in data/)
python scripts/evaluate_holdout.py --predictions docs/downloads/*.tif --data data/labels.tif
```

## License / data

Competition data is DrivenData-provided (login). Public external sources:
GeoDAWN (USGS, CC0), INGENIOUS (GDR, CC BY 4.0), USGS Quaternary Faults.
All data used must be shareable with the challenge organizers (competition
rules).
