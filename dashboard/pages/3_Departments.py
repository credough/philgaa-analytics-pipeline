import streamlit as st
from pipeline.analytics import budget_by_department
from dashboard.utils.formatters import format_peso
from dashboard.utils.charts import treemap_chart, horizontal_bar_chart
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

st.markdown("## Department Budget Distribution")
st.markdown('<p class="caption-text">Budget aggregated at the department level — FY2021 General Appropriations Act</p>', unsafe_allow_html=True)
st.markdown("---")

df = budget_by_department(fiscal_year=2021, top_n=15)

# Treemap requires a root parent node
treemap_df = df.copy()
treemap_df["parent"] = "All Departments"
treemap_df["department_short"] = treemap_df["department_name"].str[:35]

fig_tree = treemap_chart(
    df=treemap_df,
    values_col="total_appropriation",
    names_col="department_short",
    parents_col="parent",
    title="Budget Distribution by Department — FY2021",
)
st.plotly_chart(fig_tree, use_container_width=True)

fig_bar = horizontal_bar_chart(
    df=df,
    x_col="total_appropriation",
    y_col="department_name",
    title="Top 15 Departments by Appropriation — FY2021",
    x_label="Total Appropriation (PHP)",
)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("### Data Table")
display_df = df[["department_name", "department_code", "agency_count",
                  "total_appropriation", "pct_of_total"]].copy()
display_df["total_appropriation"] = display_df["total_appropriation"].apply(
    lambda x: format_peso(x)
)
display_df.columns = ["Department", "Code", "Agencies",
                       "Total Appropriation", "% of Total"]
st.dataframe(display_df, use_container_width=True, hide_index=True)