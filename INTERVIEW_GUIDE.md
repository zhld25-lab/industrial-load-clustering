# RA Interview Guide

## 60-second introduction

I built a reproducible prototype for industrial-park electricity-load pattern
analysis based on patent CN119622383A. The core question is how to identify
meaningful customer or production-line load patterns when measurements contain
errors, relationships with weather and tariff are nonlinear, and similar daily
patterns occur at shifted times. My pipeline repairs anomalies with weighted
KNN, combines KPCA global nonlinear structure with graph-based local structure,
uses DTW for time alignment, and then performs a second K-means clustering.
I compare it against a plain K-means baseline using Adjusted Rand Index on a
labeled synthetic benchmark, while clearly separating that benchmark from a
claim of real-world validation.

## Likely questions

### Why K-means?

It is fast, interpretable, and produces centroids that operations teams can
turn into representative daily load shapes. Its weaknesses—Euclidean distance,
linear geometry, and sensitivity to bad values—motivate the other stages.

### Why KPCA instead of PCA?

PCA only captures linear variance. RBF-kernel PCA can represent nonlinear
relationships among load shape, weather, price, and renewable context.

### What does KLPP contribute?

KPCA emphasizes global variance. A locality-preserving graph penalizes mappings
that separate near neighbors, retaining short-term and customer-specific
structure. The implementation uses the corresponding graph Laplacian.

### Why DTW?

Euclidean distance considers two identical peaks at 18:00 and 19:00 different.
DTW permits local temporal alignment and better recognizes the shared shape.

### What does “accuracy” mean for unsupervised learning?

There is no ordinary accuracy without labels. With known synthetic labels I use
ARI, which is invariant to cluster numbering. On real unlabeled data I would
report silhouette, stability across resamples and seasons, and operational
validation—not call silhouette “accuracy.”

### How would you use real data?

I would aggregate smart-meter readings at 15-minute resolution, join weather,
tariff, calendar, equipment, and distributed-generation data by timestamp,
prevent future leakage with time-based splits, monitor missingness and drift,
and validate clusters with facility engineers.

### What would you improve next?

Run repeated seeds and bootstrap confidence intervals, compare against
K-medoids/soft-DTW and HDBSCAN, add seasonal models, quantify peak-reduction
opportunities, and package the inference pipeline as a monitored service.

## Intellectual-honesty boundary

Do not say the attached patent supplied this Python code or dataset. Do not
claim a 21% gain unless the exact command, seed range, baseline, metric, and
result table in this repository support it. A strong answer is: “This is my
independent, reproducible implementation of the method described in the patent.”

