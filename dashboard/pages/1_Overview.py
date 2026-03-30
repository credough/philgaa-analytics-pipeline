import streamlit as st
from pipeline.analytics import budget_summary_kpis, budget_by_expense_class
from dashboard.utils.formatters import format_peso, format_number
from dashboard.utils.charts import pie_chart
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

st.header("Budget Overview")
st.caption("FY2021 headline figures and budget composition")

kpis = budget_summary_kpis(fiscal_year=2021)

st.markdown("### Key Figures")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Appropriation",
        value=format_peso(kpis["total_appropriation"]),
    )
with col2:
    st.metric(
        label="Total Agencies",
        value=format_number(kpis["total_agencies"]),
    )
with col3:
    st.metric(
        label="Total Departments",
        value=format_number(kpis["total_departments"]),
    )
with col4:
    st.metric(
        label="Total Programs",
        value=format_number(kpis["total_programs"]),
    )

st.markdown("---")
st.markdown("### Budget Composition by Expense Class")

ec_df = budget_by_expense_class(fiscal_year=2021)
fig = pie_chart(
    df=ec_df,
    values_col="total_appropriation",
    names_col="expense_class_name",
    title="Appropriation by Expense Class — FY2021",
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Expense Class Breakdown")
display_df = ec_df[["expense_class_name", "expense_class_code",
                     "total_appropriation", "pct_of_total"]].copy()
display_df["total_appropriation"] = display_df["total_appropriation"].apply(
    lambda x: format_peso(x)
)
display_df.columns = ["Expense Class", "Code", "Total Appropriation", "% of Total"]
st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("### Summary")
st.markdown(
    f"The FY2021 General Appropriations Act authorized a total budget of "
    f"**{format_peso(kpis['total_appropriation'])}** across "
    f"**{format_number(kpis['total_departments'])} departments** and "
    f"**{format_number(kpis['total_agencies'])} agencies**. "
    f"The largest expense category was **{kpis['top_expense_class']}** "
    f"at **{kpis['top_expense_class_pct']}%** of total appropriations."
)