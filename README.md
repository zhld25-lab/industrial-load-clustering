# Industrial Park Load Pattern Analysis

A reproducible Python implementation inspired by Chinese patent application
**CN119622383A**, “Method and system for industrial-park load analysis based
on optimized K-means clustering.”

> **Confidentiality and data disclosure:** the underlying industrial project
> was private, so its operational measurements, customer information, and
> facility details cannot be shared. This public repository uses a reproducible
> synthetic dataset only. The supplied patent package also contains no raw
> measurements or source code. The repository demonstrates the engineering
> method; it does not claim that its simulated results are production
> validation or a fixed 21% accuracy improvement.

## What the system does

1. Builds 24-hour load curves for three park archetypes: energy-intensive
   manufacturing, distributed-energy users, and EV charging.
2. Injects missing values and sensor anomalies for a controlled evaluation.
3. Repairs bad observations with distance-weighted KNN and applies min-max
   normalization.
4. Selects the cluster count while reporting the elbow (WCSS) curve.
5. Fuses nonlinear global KPCA features with a k-NN graph-Laplacian local
   embedding (an implementable interpretation of KPCA-KLPP).
6. Uses Dynamic Time Warping to reassign phase-shifted daily curves.
7. Runs a second K-means pass and compares it with baseline K-means using
   Adjusted Rand Index (ARI) and silhouette score.
8. Stores hourly demand, onsite generation, weather, tariff, and quality data
   in a normalized, indexed SQLite database for reproducible SQL analysis.

## Architecture

```mermaid
flowchart TD
    A["Synthetic CSV"] --> B["SQLite ingestion + validation"]
    B --> C["Load + external context"]
    C --> D["Robust anomaly marking"]
    D --> E["KNN repair + scaling"]
    E --> F["K selection + K-means"]
    F --> G["KPCA + Laplacian + DTW"]
    G --> H["Patterns + dashboard"]
```

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev,dashboard]"
industrial-load-build-db --days 30 --facilities-per-type 4 --seed 42
industrial-load-demo --seed 42
pytest
streamlit run app.py
```

The CLI writes `results/metrics.json` and `results/clustered_loads.csv`.

## Dataset and database

The public demo assets are:

- `data/synthetic_hourly_loads.csv`: a compact checked-in sample with 2,016
  hourly readings for 12 fictional facilities over 7 days. The build command
  expands it to 8,640 readings over 30 days by default.
- `data/industrial_load_demo.sqlite`: the query-ready SQLite database built
  locally from the same CSV. The binary database is reproducible and therefore
  not versioned; run `industrial-load-build-db` to create it.
- `data/README.md`: dataset card, disclosure language, field definitions, and
  appropriate-use boundaries.
- `sql/schema.sql`: normalized schema with constraints, foreign keys, indexes,
  and two analytical views.
- `sql/example_queries.sql`: reproducible peak, load-type, renewable, and
  data-quality queries.

The relational model separates `parks`, `facilities`, and
`load_measurements`. `dataset_metadata` stores the synthetic-data notice inside
the database, so the disclosure travels with the artifact rather than living
only in this README.

```bash
sqlite3 data/industrial_load_demo.sqlite
.tables
SELECT * FROM v_park_hourly_load ORDER BY net_load_kw DESC LIMIT 5;
```

## How to explain this in an RA interview

**Problem.** Industrial-park demand is heterogeneous, nonlinear, time-shifted,
and frequently incomplete. Plain Euclidean K-means is sensitive to all four.

**Design choice.** KNN repair addresses missing/error observations; KPCA models
nonlinear global structure; the graph Laplacian preserves local neighborhoods;
DTW handles the same operating pattern occurring at slightly different times.

**Evaluation.** ARI is used because cluster numbers are arbitrary and the
synthetic generator supplies hidden ground-truth archetypes. Silhouette is an
internal metric for real unlabeled deployments. These results evaluate the
prototype against simulated labels—not a real industrial park. A single
accuracy percentage without a labeled dataset, baseline, seeds, and confidence
interval would not be defensible.

**Production next step.** Replace the generator with 15-minute smart-meter,
weather, tariff, equipment, and renewable-generation feeds; fit on a time-based
training window; validate stability across seasons; then connect discovered
patterns to peak-shaving and capacity-planning rules.

## Patent-to-code traceability

| Patent stage | Repository implementation |
|---|---|
| (1) cleaning and normalization | `preprocessing.py` |
| (2) optimal cluster count / elbow | `pipeline.py::_select_k` |
| (3) initial K-means | `pipeline.py` |
| (4) KPCA-KLPP feature fusion | `features.py` |
| (5) DTW cumulative distance | `dtw.py` |
| (6) reassignment and second clustering | `pipeline.py` |
| system presentation | `app.py` |
| synthetic time-series generation | `database.py::generate_hourly_dataset` |
| relational database and views | `database.py`, `sql/schema.sql` |

## Limitations

- Synthetic profiles demonstrate mechanics, not grid readiness.
- The patent describes mathematical objectives but does not provide executable
  KLPP code or complete experimental parameters; the graph-Laplacian component
  is documented as an engineering interpretation.
- K selection uses silhouette as a reproducible tie-breaker while still
  exposing WCSS for elbow inspection.
- DTW is quadratic in curve length and should be approximated or batched for
  very large fleets.

## Reference

CN119622383A, published 2025-03-14. Applicants: Wuhan Hengda Electrical Co.,
Ltd. and Wuhan Institute of Technology.
