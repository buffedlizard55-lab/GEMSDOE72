# Repository review and evidence ledger

**Review date:** 2026-10-20 (UTC)

## Executive finding

The repository was an empty starter checkout: `README.md` was 11 bytes, with no project code, dependencies, tests, data directory, registry, generated artifact, site, or workflow at review start. Therefore the prompt's shared-tool protocol cannot currently be followed: there is no cached feature stack, `evaluate_holdout.py`, `submission_writer.py`, sample submission, or registry raster. No raster was generated, no holdout was run, no scores/CI or correlation/overlap were measured, and no submission slot should be used.

The landing page now states **NO SUBMISSION FILE — DO NOT DOWNLOAD OR SUBMIT**. That is intentional: a synthetic zero/white-noise raster would be easy to generate but would not prove unique geology, match the official grid, or correct the reported [0,1] validation problem. It would violate the project's own experiment gates.

## The 0.2778 question, answered cautiously

The cited [GEMSDOE32 page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) identifies its H33-2-B2 candidate, describes deletion of predictions near the existing catalogue, and reports owner-side validation/projection statements. It also explicitly says **“NO ORGANISER SCORE EXISTS”** for its artifacts. Thus the supplied `0.2778` is not established as an organizer-confirmed result by the fetched page. A score receipt was not available in this checkout.

A plausible mechanism—**not proven to explain 0.2778**—is that the official DTI penalizes missed positives more heavily than false positives (beta 0.8 versus alpha 0.2) and gives partial credit within the 300 m triangular support. A compact line-like probability field can improve efficiency if it allocates probability near true fault pixels while avoiding diffuse mass. But whether the named raster did that requires its actual bytes, official labels/holdout context, and receipt. The sibling page's claimed holdout projections do not substitute for an organizer score. The `-zeros` suffix is not enough evidence to infer raster content or cause.

### Conflicting score statements resolved by source class

- The official [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) fetched 2026-10-20 lists the top public DW-Tversky score as **0.4413**. This is **ORGANIZER-CONFIRMED as a public leaderboard listing**, not as a score for this project.
- The owner-provided prompt's `0.3195` is stale relative to that fetched listing.
- The `0.2778` attributed to a GEMSDOE32 file is **owner/site-reported**, not organizer-confirmed according to the page itself.
- Scores seen in sibling websites are not assumed to be the official leaderboard, receipts, or comparable holdout results. They must retain their source labels.

The leaderboard is time-dependent; re-fetch it when reporting a future status. The first team entry and current score do not imply that a particular raster method is public or reproducible.

## Official specifications checked

1. **[DrivenData problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)**: describes the incomplete-catalogue discovery task, distance-weighted Tversky metric, alpha 0.2, beta 0.8, 300 m triangular distance support, and GeoTIFF submission requirements. The official page states EPSG:32611, 100 m, same bounds/grid as training data, one band, float32, values in [0,1], and null/NaN outside the bounds.
2. **[DrivenData about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)**: explains the survey context, the role of faults in geothermal systems, and that GeoDAWN includes airborne magnetic/radiometric information and coordinated lidar coverage. It also cites fault-mapping literature and describes the task.
3. **[DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)**: live public scores and submission counts; fetched 2026-10-20. Treat as a dated snapshot, not immutable.
4. **[USGS GeoDAWN page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)**: identifies the GeoDAWN airborne magnetic/radiometric survey and links the USGS data release DOI 10.5066/P93LGLVQ. The page itself describes high-resolution surveys and associated product types.
5. **[GDR INGENIOUS dataset 1391](https://gdr.openei.org/submissions/1391)**: labels the compilation publicly accessible under CC BY 4.0, DOI 10.15121/1881483, and lists downloadable resources including 2 m temperature probes, earthquake density models, paleogeothermal features, quaternary faults, and well/spring chemistry. The listing is verified from the fetched page; actual files were not downloaded or inspected here.
6. **[Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)** and [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) are linked for further manual review. Their contents were not needed to create a raster in this pass.

## Irregularities / risks flagged

- **Missing assets are a hard blocker.** Competition training data is login-gated (as noted by the project owner); this checkout contains none. No authenticated download or user credentials were attempted or requested.
- **Shared tooling absent.** The request explicitly says reuse cached stack/evaluator/writer and fix shared problems in the template. There is no such code in this repository, so implementing a private substitute would violate the protocol.
- **Registry absent.** Cannot test the duplicate thresholds against any previous submission rasters. File names and descriptions are not adequate substitutes for pixel comparisons.
- **Score provenance conflict.** The sibling site calls its file a candidate and says there is no organizer score; the prompt lists 0.2778 as a result. Do not present it as organizer-confirmed without the receipt.
- **Old stated leader.** The official page fetched on review date lists 0.4413, superseding the 0.3195 claim. The contest page may change.
- **Prior-art overlap.** The fetched GEMSDOE32 hypotheses page discusses related thermal-probe, MT, seismicity, and paleothermal ideas. This repo has none of those implementations, but we cannot claim the ideas are novel across sibling repositories. Similarity is disclosed in the candidate register.
- **Lane text is underspecified.** The request says “single method paragraph below” but does not supply a uniquely delimited method paragraph to define the lane. No experiment was selected by guessing at the intended lane.
- **No blocked holdout can be derived.** Without actual labels, exact grid, fault-segment geometry and shared evaluator, a meaningful holdout DTI/CI or leakage test would be fabricated.
- **No TIF was produced.** A unique filename or new byte hash would not establish a unique scientific strategy or a valid upload. This is deliberate.
- **Leaderboard freshness is not guaranteed until Pages Actions runs.** A daily workflow now attempts to fetch the official public listing and redeploy the site; if parsing/fetching fails it retains the last checked-in JSON snapshot and emits a warning. The displayed date must therefore be checked, not assumed current.

## Pass checklist

### Pass 1 — implement

Created the README project charter, a landing page with a prominent negative readiness status, an executive-summary submission guide, and a candidate hypothesis register. No model/raster code was added because all necessary inputs and shared tools are absent.

### Pass 2 — audit

Checked that no download link or false “ready” claim is shown; the 0.2778 number has a clear non-organizer label; the live 0.4413 is a dated official leaderboard listing; hypotheses state method, layers, physical rationale, mimic, difference, cost, and external-source status; none is represented as tested. Confirmed the site is plain static HTML/Markdown and requires no hidden data/service.

### Pass 3 — final cross-check

Rechecked the submission requirements against the official problem page, verified current leaderboard and source availability listings through official pages, and ensured the run card records null for unmeasured values and verdict `negative` (not eligible). Outcome: repository review and documentation are complete; scientific validation and a safe TIF are blocked.

## Suggested next work

1. Restore the authorized competition data files and official sample into `data/`; record provenance, file sizes, and hashes. Keep restricted/private files out of public Git if the competition's terms require it.
2. Bring the canonical shared template/toolchain into this branch (or connect it as intended), including the cached feature stack, `evaluate_holdout.py`, `submission_writer.py`, registry rasters, and format validation tests. Do not fork a private evaluator/writer.
3. Recheck the workflow and constraints at session start; inspect source inventories and prior art before selecting one candidate. Verify the proposed source's actual fields, CRS, footprint, license, and temporal relevance.
4. Preregister candidate and split; run no more than three experiments or two hours; conduct feature-alone leakage canaries; compute pooled spatial-blocked holdout DTI and bootstrap 95% CI with evaluator version and withheld-positive count.
5. Run pre-placement and final-dot registry duplicate checks. On failure, document as duplicate and stop.
6. Only after holdout and format gates pass, generate one uniquely named candidate TIF from the shared writer, reopen it for independent validation, calculate SHA-256, and update the landing page. Submission-slot selection remains a separate decision.
7. A GitHub Pages Actions workflow is now included and publishes only `index.html` and `docs/` on pushes to `main`. Deployment was not run in this local review; repository Pages settings must allow GitHub Actions, and remote settings were not changed.
