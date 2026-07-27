# Reproducible benchmark

The benchmark is a controlled mechanism test, not evidence of production
performance. It uses 90 synthetic facilities, three hidden archetypes, random
clock shifts, missing readings, and injected sensor errors.

Run:

```bash
industrial-load-demo --seed 42
```

Expected seed-42 result with version 1.0:

| Metric | Baseline | Optimized |
|---|---:|---:|
| Adjusted Rand Index | 0.562 | 0.653 |
| Silhouette | 0.270 | 0.320 |

The ARI relative change is 16.37% for this seed. Across seeds 0-9 during the
development validation, the mean ARI was approximately 0.596 for baseline and
0.758 for the optimized pipeline, with the optimized pipeline winning 8 of 10
runs. These are deterministic synthetic results, not a claim that every real
industrial dataset will improve.

## Why the result is not forced to 21%

A percentage is meaningful only with a specified dataset, baseline, metric,
random-seed policy, and uncertainty analysis. The supplied patent documents do
not contain an auditable table supporting a 21% claim. This repository reports
what its executable experiment produces.

