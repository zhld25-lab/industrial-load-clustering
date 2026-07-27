import json
import sys

import numpy as np
import pandas as pd

from industrial_load import cli, database


def test_experiment_run_writes_reproducible_outputs(tmp_path):
    first = cli.run(seed=42, output=tmp_path / "first")
    second = cli.run(seed=42, output=tmp_path / "second")
    assert first.keys() == second.keys()
    for key in first:
        if isinstance(first[key], float):
            assert np.isclose(first[key], second[key])
        else:
            assert first[key] == second[key]
    assert first["samples"] == 90
    assert 2 <= first["selected_clusters"] <= 6
    assert (tmp_path / "first" / "metrics.json").exists()
    clustered = pd.read_csv(tmp_path / "first" / "clustered_loads.csv")
    assert len(clustered) == 90
    assert {"true_pattern", "predicted_cluster"} <= set(clustered.columns)


def test_cli_entry_point(monkeypatch, tmp_path, capsys):
    output = tmp_path / "experiment"
    monkeypatch.setattr(
        sys, "argv", ["industrial-load-demo", "--seed", "7", "--output", str(output)]
    )
    cli.main()
    printed = json.loads(capsys.readouterr().out)
    assert printed["seed"] == 7
    assert output.joinpath("metrics.json").exists()


def test_database_cli_entry_point(monkeypatch, tmp_path, capsys):
    output = tmp_path / "assets"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "industrial-load-build-db",
            "--output-dir",
            str(output),
            "--days",
            "1",
            "--facilities-per-type",
            "1",
            "--seed",
            "5",
        ],
    )
    database.main()
    printed = capsys.readouterr().out
    assert database.DATA_NOTICE in printed
    assert output.joinpath("synthetic_hourly_loads.csv").exists()
    assert output.joinpath("industrial_load_demo.sqlite").exists()
