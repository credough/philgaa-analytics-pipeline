from pipeline.analytics import (
    total_budget_by_agency,
    budget_by_expense_class,
    budget_by_department,
    top_programs_by_budget,
    budget_summary_kpis,
)

print("--- Top 5 Agencies ---")
print(total_budget_by_agency(top_n=5).to_string(index=False))

print("\n--- Expense Class Breakdown ---")
print(budget_by_expense_class().to_string(index=False))

print("\n--- Top 5 Departments ---")
print(budget_by_department(top_n=5).to_string(index=False))

print("\n--- Top 5 Programs ---")
print(top_programs_by_budget(top_n=5).to_string(index=False))

print("\n--- KPIs ---")
kpis = budget_summary_kpis()
for k, v in kpis.items():
    print(f"  {k}: {v}")