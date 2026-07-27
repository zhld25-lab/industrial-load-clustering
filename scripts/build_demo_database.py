"""Generate the public synthetic CSV and SQLite demo database."""

from __future__ import annotations

import argparse

from industrial_load.database import DATA_NOTICE, export_demo_assets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--facilities-per-type", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    csv_path, db_path = export_demo_assets(
        args.output_dir, args.days, args.facilities_per_type, args.seed
    )
    print(DATA_NOTICE)
    print(f"CSV: {csv_path}")
    print(f"SQLite: {db_path}")


if __name__ == "__main__":
    main()
