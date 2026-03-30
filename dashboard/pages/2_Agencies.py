import streamlit as st
from pipeline.analytics import total_budget_by_agency
from dashboard.utils.formatters import format_peso
from dashboard.utils.charts import horizontal_bar_chart
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

st.header("Agency Budget Rankings")
st.caption("Top agencies by authorized appropriation — FY2021")

top_n = st.slider("Number of agencies to display", min_value=5,
                   max_value=30, value=15, step=5)

df = total_budget_by_agency(fiscal_year=2021, top_n=top_n)

fig = horizontal_bar_chart(
    df=df,
    x_col="total_appropriation",
    y_col="agency_name",
    title=f"Top {top_n} Agencies by Appropriation — FY2021",
    x_label="Total Appropriation (PHP)",
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Data Table")
display_df = df[["rank", "agency_name", "department_name",
                  "total_appropriation"]].copy()
display_df["total_appropriation"] = display_df["total_appropriation"].apply(
    lambda x: format_peso(x)
)
display_df.columns = ["Rank", "Agency", "Department", "Total Appropriation"]
st.dataframe(display_df, use_container_width=True, hide_index=True)