import streamlit as st
from pipeline.analytics import top_programs_by_budget
from dashboard.utils.formatters import format_peso, truncate_label
from dashboard.utils.charts import horizontal_bar_chart
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

st.markdown("## Top Programs by Budget")
st.markdown('<p class="caption-text">Highest-appropriated programs and projects — FY2021 General Appropriations Act</p>', unsafe_allow_html=True)
st.markdown("---")

top_n = st.slider("Number of programs to display", min_value=5,
                   max_value=25, value=10, step=5)

df = top_programs_by_budget(fiscal_year=2021, top_n=top_n)

fig = horizontal_bar_chart(
    df=df,
    x_col="total_appropriation",
    y_col="project_name",
    title=f"Top {top_n} Programs by Appropriation — FY2021",
    x_label="Total Appropriation (PHP)",
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Data Table")
display_df = df[["rank", "project_name", "agency_name",
                  "total_appropriation"]].copy()
display_df["total_appropriation"] = display_df["total_appropriation"].apply(
    lambda x: format_peso(x)
)
display_df.columns = ["Rank", "Program", "Agency", "Total Appropriation"]
st.dataframe(display_df, use_container_width=True, hide_index=True)