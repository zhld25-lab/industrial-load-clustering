# Synthetic Dataset Card

## Disclosure

**This repository contains synthetic data only.** The original industrial
project was private, so its operational measurements, customer identifiers,
facility details, and commercial context cannot be disclosed. Every facility,
timestamped reading, label, anomaly, weather value, and tariff value here was
generated for demonstration. The data must not be described as measured,
anonymized, or production data.

Recommended interview wording:

> The original project was private and subject to confidentiality constraints,
> so I cannot share its operational data. To demonstrate the engineering
> workflow without exposing protected information, I built a reproducible
> synthetic dataset with similar schema and load-pattern characteristics. All
> results in this repository apply only to the simulated dataset.

## Files

- `synthetic_hourly_loads.csv`: denormalized, analysis-ready hourly records.
- `industrial_load_demo.sqlite`: normalized, indexed SQLite database generated
  locally from the same records. It is reproducible and not stored in Git.

The checked-in sample contains 12 fictional facilities, three load-pattern
types, and 7 days of hourly records (2,016 rows). The default rebuild expands
the time window to 30 days (8,640 rows):

```bash
python scripts/build_demo_database.py --days 30 --facilities-per-type 4 --seed 42
```

## Important fields

| Field | Meaning |
|---|---|
| `facility_type` | Hidden synthetic archetype used only for controlled evaluation |
| `gross_load_kw` | Simulated facility demand before onsite generation |
| `renewable_generation_kw` | Simulated onsite solar generation |
| `net_load_kw` | Simulated grid-facing demand |
| `tariff_usd_kwh` | Illustrative time-of-use tariff, not a utility quote |
| `quality_flag` | `valid`, deliberately injected `anomaly`, or `missing` |
| `data_source` | Always `synthetic_generator_v1` |

## Intended and prohibited uses

Suitable for schema demonstrations, SQL exercises, dashboard development,
pipeline testing, and clustering evaluation. It is not suitable for grid
planning, billing, equipment sizing, safety decisions, or claims about a real
industrial park.
