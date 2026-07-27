"""Streamlit interview demo with database-backed load analytics."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from industrial_load.cli import run
from industrial_load.database import DATA_NOTICE, export_demo_assets, read_query


st.set_page_config(page_title="Industrial Load Intelligence", layout="wide")
st.title("Industrial Park Load Pattern Intelligence")
st.caption("Patent-aligned reproducible prototype based on CN119622383A")
st.warning(
    "Confidentiality disclosure: the original project was private. "
    "This demo uses synthetic data only; no real facility or customer data is included."
)

data_dir = Path("data")
database_path = data_dir / "industrial_load_demo.sqlite"
if not database_path.exists():
    export_demo_assets(data_dir)

overview_tab, cluster_tab, database_tab = st.tabs(
    ["Load overview", "Clustering experiment", "Database explorer"]
)

with overview_tab:
    hourly = read_query(
        database_path,
        """
        SELECT timestamp, gross_load_kw, renewable_generation_kw, net_load_kw
        FROM v_park_hourly_load
        ORDER BY timestamp
        """,
    )
    hourly["timestamp"] = pd.to_datetime(hourly["timestamp"])
    peak = hourly.loc[hourly["net_load_kw"].idxmax()]
    quality = read_query(
        database_path,
        """
        SELECT quality_flag, COUNT(*) AS records
        FROM load_measurements
        GROUP BY quality_flag
        ORDER BY records DESC
        """,
    )
    facility_count = int(
        read_query(database_path, "SELECT COUNT(*) AS n FROM facilities").iloc[0]["n"]
    )

    cols = st.columns(4)
    cols[0].metric("Synthetic facilities", facility_count)
    cols[1].metric("Hourly records", f"{len(hourly) * facility_count:,}")
    cols[2].metric("Synthetic peak", f'{peak["net_load_kw"]:,.0f} kW')
    cols[3].metric(
        "Renewable share",
        f'{100 * hourly["renewable_generation_kw"].sum() / hourly["gross_load_kw"].sum():.1f}%',
    )

    chart_data = hourly.melt(
        id_vars="timestamp",
        value_vars=["gross_load_kw", "renewable_generation_kw", "net_load_kw"],
        var_name="series",
        value_name="power_kw",
    )
    st.plotly_chart(
        px.line(
            chart_data,
            x="timestamp",
            y="power_kw",
            color="series",
            title="Synthetic park-wide load and onsite generation",
        ),
        use_container_width=True,
    )
    st.dataframe(quality, use_container_width=True, hide_index=True)

with cluster_tab:
    seed = st.number_input("Random seed", min_value=0, value=42)
    if st.button("Run clustering analysis", type="primary"):
        st.session_state["metrics"] = run(int(seed))

    if "metrics" in st.session_state:
        metrics = st.session_state["metrics"]
        cols = st.columns(4)
        cols[0].metric("Profiles", metrics["samples"])
        cols[1].metric("Selected clusters", metrics["selected_clusters"])
        cols[2].metric("Baseline ARI", f'{metrics["baseline_ari"]:.3f}')
        cols[3].metric("Optimized ARI", f'{metrics["optimized_ari"]:.3f}')
        clustered = pd.read_csv("results/clustered_loads.csv")
        load_cols = [column for column in clustered if column.startswith("load_h")]
        long = clustered.melt(
            id_vars=["predicted_cluster"],
            value_vars=load_cols,
            var_name="hour",
            value_name="load_kw",
        )
        long["hour"] = long["hour"].str.extract(r"(\d+)").astype(int)
        means = long.groupby(["predicted_cluster", "hour"], as_index=False)["load_kw"].mean()
        st.plotly_chart(
            px.line(
                means,
                x="hour",
                y="load_kw",
                color="predicted_cluster",
                title="Mean 24-hour profile by discovered synthetic cluster",
            ),
            use_container_width=True,
        )
        st.caption(
            "ARI is available because the generator creates hidden labels. "
            "It would not be available for unlabeled operational data."
        )
    else:
        st.info("Choose a seed and run the clustering experiment.")

with database_tab:
    st.code(
        """
SELECT f.facility_type,
       ROUND(AVG(m.net_load_kw), 2) AS average_net_load_kw,
       ROUND(MAX(m.net_load_kw), 2) AS peak_net_load_kw
FROM load_measurements AS m
JOIN facilities AS f USING (facility_id)
WHERE m.quality_flag <> 'missing'
GROUP BY f.facility_type;
        """.strip(),
        language="sql",
    )
    summary = read_query(
        database_path,
        """
        SELECT f.facility_type,
               ROUND(AVG(m.net_load_kw), 2) AS average_net_load_kw,
               ROUND(MAX(m.net_load_kw), 2) AS peak_net_load_kw,
               ROUND(SUM(m.renewable_generation_kw), 2) AS renewable_energy_kwh
        FROM load_measurements AS m
        JOIN facilities AS f USING (facility_id)
        WHERE m.quality_flag <> 'missing'
        GROUP BY f.facility_type
        ORDER BY peak_net_load_kw DESC
        """,
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)
    st.caption(DATA_NOTICE)
