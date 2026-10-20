# Candidate hypotheses — registered, not yet tested

**Decision:** no experiment was run and no weekly submission slot is recommended. This checkout has no input data, cached features, shared evaluator/writer, or registry rasters; therefore no holdout ranking, leakage canary, duplicate check, or DTI improvement can be measured. Candidate rank below is qualitative expected value per implementation cost, not a predicted score.

## Scope and novelty caution

The working tree at review time was empty except for an 11-byte README. “Different from this repository” therefore means no current implementation exists here. The owner supplied a long history of experiments from sibling GEMSDOE sites; a fetched GEMSDOE32 hypotheses page describes related thermal-probe, paleothermal, seismicity, and structural ideas. **These candidates cannot be claimed globally novel across the sibling sites.** They are ranked as not-yet-implemented variants for this checkout, with overlap disclosed so the team can avoid accidental duplication. This is a research register, not a submission roster.

## Ranked candidates

| Rank | Hypothesis / layers | Physical signature and missing-catalogue rationale | Difference from code in this checkout / prior-family overlap | Expected benefit / cost / external data status |
|---|---|---|---|---|
| 1 | **Survey-adjusted shallow thermal residual lineaments.** INGENIOUS 2-m temperature-probe observations from GDR 1391, with the official supplied terrain/geophysical layers only as independent corroborators. | Remove documented sampling covariates (only if present in the delivered schema, such as location/elevation or survey timing); detect spatially coherent residual thermal highs/gradients rather than thresholding raw temperatures; require line-shaped continuity and non-fault corroboration. Shallow thermal anomalies could indicate fluid discharge on concealed structures; the mimic is solar exposure, soil moisture, season, or land-cover variation. | No code exists in this checkout. The related GEMSDOE32 page previously registered a simpler probe-anomaly mask (H33-3), so this is a distinct residualisation/lineament operator, **not a globally novel data source or established new lane**. Data page lists the 2m probe ZIP (1.03 MB) as downloadable. Schema and actual bytes remain uninspected here. | **Moderate potential / medium cost.** Official source is public and directly lists a download: [GDR submission 1391](https://gdr.openei.org/submissions/1391), resource [2m temperature probe ZIP](https://gdr.openei.org/files/1391/2m_temperature_probe_INGENIOUS_regional_data.zip). Viability is conditional on schema/coverage review and no data leakage. No score estimate. |
| 2 | **Depth-persistent MT conductance edges.** Public GDR/USGS magnetotelluric electrical-conductance maps at multiple depth ranges, plus the supplied structural/geophysical context. | Extract orientation-coherent boundaries that persist across several depth slices, not a single conductance anomaly. A persistent subsurface boundary beneath basin fill could mark a fault not expressed as a mapped surface trace. The mimic is lithologic/contact contrast or non-fault basin geometry. | No code exists in this checkout. Sibling work described a long-straight conductance/basement-boundary family (H33-D), so a multi-depth persistence test is related and cannot be marketed as globally new. GDR 1391 lists an electrical-conductance dataset by DOI, but the actual files/coverage must be checked before use. | **Moderate potential / medium-high cost.** Official resource is linked at [GDR 1391](https://gdr.openei.org/submissions/1391), under “Electrical Conductance Maps - MT” (DOI [10.5066/P9TWT2LU](https://doi.org/10.5066/P9TWT2LU)). Page availability verified; direct data retrieval/footprint match not verified. No score estimate. |
| 3 | **Directional ridge coherence of the official earthquake-density field.** INGENIOUS seismicity density products from GDR 1391, optionally checked against the supplied earthquake-density bands. | Detect elongated, directionally coherent seismicity structures rather than broad high-density blobs, and test whether their orientation is spatially stable across scale. A seismic lineament may reveal a buried/low-scarp fault absent from surface mapping. The mimic is clustered seismicity on a non-fault structure or survey/network-density artifacts. | No code exists in this checkout. A related seismicity-coherence idea appears in the fetched GEMSDOE32 research register (H61-2), so this candidate is explicitly not globally novel; it is an unvalidated proposal here. GDR lists a 22.98 MB earthquake-density ZIP. | **Low-to-moderate potential / medium cost.** Official listing and download link verified at [GDR 1391](https://gdr.openei.org/submissions/1391), resource [earthquake-density ZIP](https://gdr.openei.org/files/1391/seismicity_INGENIOUS_regional_data.zip). Actual grids, resolution, and overlap with training features have not been checked. No score estimate. |
| 4 | **Paleo-geothermal evidence conditioned on independent structural alignment.** INGENIOUS paleogeothermal spring deposits (sinter, tufa, and related mapped features) from GDR 1391, coupled to supplied geophysical lineaments. | Instead of emitting a radial proximity halo around deposits, test whether multiple mapped paleo-geothermal features align along an independently detected structural trend and emit only on the supported segment. This targets fossil fluid pathways not necessarily represented in a fault catalogue. The mimic is non-tectonic spring deposition, drainage-controlled carbonate, or clustered data collection. | No code exists in this checkout. The GDR resource is already proposed as a broad prior by the sibling GEMSDOE32 page (H33-4); the line-alignment rule differs from that simple prior, but this is a related family and cannot be called globally new. | **Low potential / low-medium cost.** GDR 1391 explicitly lists a downloadable 82.04 kB [Paleo Geothermal Features ZIP](https://gdr.openei.org/files/1391/paleo_geothermal_regional.zip) under a publicly accessible CC BY 4.0 dataset. Geometry, attribution, footprint, and duplicate overlap still need to be verified. No score estimate. |

## Promotion gate (not yet run)

1. Restore the shared cached stack, `evaluate_holdout.py`, `submission_writer.py`, sample submission, visible-fault labels, and registry rasters. Do not make a private fork if the canonical shared versions exist elsewhere.
2. Before placement, compare candidate surface and final dots against every registry raster. Rank correlation `>0.90` or `>70%` of dots within 3 px of one registry raster is a duplicate: log it and stop. These checks cannot be inferred from file names or narrative reports.
3. Register one candidate and all thresholds before evaluation. Hold out whole fault segments with a buffer; derive catalogue-based features only from the visible faults; pixel-exactly mask visible positives; pool DTI using the official alpha 0.2, beta 0.8 and 300 m triangular kernel. The holdout report must include evaluator version, withheld-positive count, and 95% CI.
4. Run each feature alone as a leakage canary. AUC above 0.90 is treated as leakage until investigated.
5. Do not spend a weekly slot unless the candidate beats the current holdout best under the preregistered criterion and has no leakage/duplicate failure. Maximum three experiments or two hours.

## Run card for this review

```json
{
  "hypothesis": "No candidate evaluated; checkout lacks the shared stack and evaluator",
  "mechanism": "Not tested",
  "named_non_fault_mimic": "Not assessed; candidate-specific mimics are listed above",
  "holdout_dti_ci": null,
  "holdout_evaluator_version": null,
  "withheld_positive_count": null,
  "registry_correlation_overlap": null,
  "raster_sha256": null,
  "validator": "NOT RUN: no sample grid, raster, or writer present",
  "submission_name": null,
  "submission_note": null,
  "verdict": "negative"
}
```

Here `negative` means **not eligible / no evidence**, not a measured negative DTI result. No score or projection is supplied.
