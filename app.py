"""Streamlit interview demo."""

import pandas as pd
import plotly.express as px
import streamlit as st

from industrial_load.cli import run

st.set_page_config(page_title="Industrial Load Intelligence", layout="wide")
st.title("Industrial Park Load Pattern Intelligence")
st.caption("Patent-aligned reproducible prototype based on CN119622383A")

seed = st.sidebar.number_input("Random seed", min_value=0, value=42)
if st.sidebar.button("Run analysis", type="primary"):
    metrics = run(int(seed))
    st.session_state["metrics"] = metrics

if "metrics" in st.session_state:
    m = st.session_state["metrics"]
    cols = st.columns(4)
    cols[0].metric("Facilities", m["samples"])
    cols[1].metric("Selected clusters", m["selected_clusters"])
    cols[2].metric("Baseline ARI", f'{m["baseline_ari"]:.3f}')
    cols[3].metric("Optimized ARI", f'{m["optimized_ari"]:.3f}')
    data = pd.read_csv("results/clustered_loads.csv")
    load_cols = [c for c in data if c.startswith("load_h")]
    long = data.melt(id_vars=["predicted_cluster"], value_vars=load_cols, var_name="hour", value_name="load_kw")
    long["hour"] = long["hour"].str.extract(r"(\d+)").astype(int)
    means = long.groupby(["predicted_cluster", "hour"], as_index=False)["load_kw"].mean()
    st.plotly_chart(px.line(means, x="hour", y="load_kw", color="predicted_cluster",
                            title="Mean 24-hour load profile by discovered cluster"), use_container_width=True)
else:
    st.info("Choose a seed and run the analysis.")

