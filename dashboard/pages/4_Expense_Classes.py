import streamlit as st
from pipeline.analytics import budget_by_expense_class, total_budget_by_agency
from dashboard.utils.formatters import format_peso
from dashboard.utils.charts import horizontal_bar_chart, pie_chart
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

st.markdown("## Expense Class Analysis")
st.markdown('<p class="caption-text">Breakdown by Personnel Services, MOOE, Capital Outlay, and Financial Expenses — FY2021</p>', unsafe_allow_html=True)
st.markdown("---")

ec_df = budget_by_expense_class(fiscal_year=2021)

col1, col2 = st.columns(2)

with col1:
    fig_pie = pie_chart(
        df=ec_df,
        values_col="total_appropriation",
        names_col="expense_class_name",
        title="Share by Expense Class",
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    fig_bar = horizontal_bar_chart(
        df=ec_df,
        x_col="total_appropriation",
        y_col="expense_class_name",
        title="Total by Expense Class",
        x_label="Total Appropriation (PHP)",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("### Breakdown Table")
display_df = ec_df[["expense_class_name", "expense_class_code",
                     "total_appropriation", "pct_of_total"]].copy()
display_df["total_appropriation"] = display_df["total_appropriation"].apply(
    lambda x: format_peso(x)
)
display_df.columns = ["Expense Class", "Code", "Total Appropriation", "% of Total"]
st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown(
    "**Personnel Services (PS)** covers salaries and compensation of government personnel. "
    "**MOOE** covers day-to-day operational costs. "
    "**Capital Outlay (CO)** covers acquisition of long-term assets. "
    "**Financial Expenses (FE)** covers debt service and interest payments."
)