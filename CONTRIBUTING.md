# How to work in this repository (read this before touching anything)

## The one rule that matters

**No number appears on the site or in the README unless it traces to a file in `registry/` or
`evidence/`, and no score is described as verified unless it was read from the public leaderboard
page in this repository.** Owner-reported scores are labelled *claim*. This is the "no
hallucinations, verify line by line" rule made mechanical.

## Data

All competition rasters are fetched through `scripts/fetch_data.py`, which verifies a SHA-256 from
`registry/data_manifest.json` and refuses nothing silently. If a digest does not match, the script
prints FAIL and exits non-zero; **never** relax the digest to make a run pass — investigate and add
an irregularity entry instead. Large rasters are never committed (`.gitignore`).

## Adding a hypothesis

1. Add an entry to `src/gemsdoe72/hypotheses.py` (layers, signature, why-off-catalogue,
   differs-from-repo, expected gain, cost, data status) and regenerate
   `registry/hypotheses.json`.
2. If it needs external data, name the free official source and its licence, and record whether it
   was actually fetched (`status`: fetched / listed-not-fetched).
3. Write the protocol into `registry/preregistration.json` **before** the run, then embed the same
   dict in the run's evidence JSON.
4. Score it on the blocked holdout at matched mass; append the evaluation to
   `registry/observations.jsonl` whether or not it wins.
5. Only `bo.slot_gate` can approve spending one of the three weekly slots, and it must be told the
   slot cost and the two-round objective.

## Review passes

Every session ends with: (Pass 1) implement + verify; (Pass 2) hunt bugs, wrong assumptions and edge
cases and fix them; (Pass 3) re-read the owner's brief and verify the deliverable against it,
including the site rendering. Record what still fails in the irregularity register and in the
README's limitations section.

## Never

* never automate access to the competition host (`drivendata.org`); the feed workflow skips it;
* never present the holdout as a score, or a proxy as the objective;
* never spend a slot on a candidate that has not beaten the incumbent at matched mass.
