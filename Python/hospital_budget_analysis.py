# ============================================================
# Hospital Expenditure Analysis & 2025 Budget Forecast
# Tools: Python (pandas, matplotlib)
# Dataset: 3 departments | 2023-2024 actual | 2025 forecast
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')


# ── LOAD DATA ────────────────────────────────────────────────

df = pd.read_excel("Budget_Forecasting_Dataset.xlsx")
print("Dataset loaded:", df.shape)
print(df.head())


# ── BASIC EXPLORATION ────────────────────────────────────────

print("\nDepartments:", df['Department'].unique())
print("Years:", df['Year'].unique())
print("Nulls:\n", df.isnull().sum())
print("\nSummary stats:\n", df.describe())


# ── DATA CLEANING ────────────────────────────────────────────

# Fix date column to proper datetime
df['Date'] = pd.to_datetime(df['Date'])

# Standardise department names
df['Department'] = df['Department'].str.strip()

# Add month label for readability
df['Month'] = df['Date'].dt.strftime('%b %Y')

print("\nData types after cleaning:\n", df.dtypes)
print("Duplicates:", df.duplicated().sum())


# ── FEATURE ENGINEERING ──────────────────────────────────────
# Creating columns that the raw data doesn't have
# These are used in the Power BI dashboard

# Budget column — hospitals typically plan budgets lower than actual spend
# ICU consistently overspends, Radiology moderately, General Ward is most controlled
np.random.seed(42)
budget_map = {
    'ICU':          0.89,   # ICU budgeted at 89% of actual (always overspends)
    'Radiology':    0.92,   # Radiology budgeted at 92%
    'General Ward': 0.94    # General Ward most controlled
}
df['Budget'] = df.apply(
    lambda row: round(row['Expenditure'] * (budget_map[row['Department']] + np.random.uniform(-0.02, 0.02)), 2),
    axis=1
)

# Variance: how much actual spend exceeded the budget
df['Variance'] = (df['Expenditure'] - df['Budget']).round(2)

# Variance %: how far over or under budget as a percentage
df['Variance_Pct'] = (df['Variance'] / df['Budget'] * 100).round(2)

# Budget status label
df['Budget_Status'] = df['Variance_Pct'].apply(
    lambda x: 'Over Budget' if x > 8 else ('Under Budget' if x < -5 else 'On Track')
)

# Month-on-Month growth %
df = df.sort_values(['Department', 'Date']).reset_index(drop=True)
df['MoM_Growth_Pct'] = (
    df.groupby('Department')['Expenditure']
    .pct_change() * 100
).round(2)

print("\nEngineered columns added:")
print(df[['Date', 'Department', 'Expenditure', 'Budget', 'Variance_Pct', 'Budget_Status']].head(6))


# ── KEY METRICS ──────────────────────────────────────────────
# These match the KPI cards on the Power BI dashboard

total_expenditure = df['Expenditure'].sum()
avg_mom_growth    = df['MoM_Growth_Pct'].dropna().mean()
top_dept          = df.groupby('Department')['Expenditure'].sum().idxmax()

print("\n" + "="*45)
print("  HOSPITAL EXPENDITURE — KEY METRICS")
print("="*45)
print(f"  Total Expenditure (2023-24): ₹{total_expenditure}L")
print(f"  Avg MoM Growth:              {avg_mom_growth:.2f}%")
print(f"  Highest Spending Dept:       {top_dept}")
print("="*45)


# ── ANALYSIS 1: TOTAL EXPENDITURE BY DEPARTMENT ──────────────
# Matches: 'Total Expenditure by Department' donut chart

dept_total = df.groupby('Department')['Expenditure'].sum().sort_values(ascending=False)
dept_pct   = (dept_total / dept_total.sum() * 100).round(1)

print("\nExpenditure by Department:")
for dept in dept_total.index:
    print(f"  {dept}: ₹{dept_total[dept]}L ({dept_pct[dept]}%)")

# Chart
plt.figure(figsize=(7, 5))
colors = ['#1B6CA8', '#F59E0B', '#22C55E']
plt.bar(dept_total.index, dept_total.values, color=colors)
plt.title("Total Expenditure by Department (2023-24)", fontweight='bold')
plt.ylabel("Expenditure (₹ Lakhs)")
for i, (val, pct) in enumerate(zip(dept_total.values, dept_pct.values)):
    plt.text(i, val + 10, f"₹{val}L\n({pct}%)", ha='center', fontsize=9)
plt.tight_layout()
plt.savefig("dept_expenditure.png", dpi=120)
plt.show()


# ── ANALYSIS 2: YEAR-ON-YEAR GROWTH ──────────────────────────
# Matches: 'Total Expenditure by Department and Year' bar chart

yearly = df.groupby(['Department', 'Year'])['Expenditure'].sum().reset_index()

print("\nYear-on-Year Growth:")
for dept in df['Department'].unique():
    d = yearly[yearly['Department'] == dept]
    y2023 = d[d['Year'] == 2023]['Expenditure'].values[0]
    y2024 = d[d['Year'] == 2024]['Expenditure'].values[0]
    growth = ((y2024 - y2023) / y2023 * 100).round(1)
    print(f"  {dept}: ₹{y2023}L (2023) → ₹{y2024}L (2024) | YoY growth: {growth}%")


# ── ANALYSIS 3: MONTHLY EXPENDITURE TREND ────────────────────
# Matches: 'Expenditure by Year and Department' line chart

plt.figure(figsize=(11, 5))
dept_colors = {'ICU': '#1B6CA8', 'Radiology': '#F59E0B', 'General Ward': '#22C55E'}

for dept, color in dept_colors.items():
    d = df[df['Department'] == dept].sort_values('Date')
    plt.plot(d['Date'], d['Expenditure'], marker='o', markersize=3,
             color=color, linewidth=2, label=dept)

plt.title("Monthly Expenditure Trend by Department (2023-24)", fontweight='bold')
plt.xlabel("Month")
plt.ylabel("Expenditure (₹ Lakhs)")
plt.legend()
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig("monthly_trend.png", dpi=120)
plt.show()


# ── ANALYSIS 4: MoM GROWTH SUMMARY ───────────────────────────
# Matches: 'Monthly Expenditure Summary with MoM Growth' table

mom_summary = df[['Month', 'Department', 'Expenditure', 'MoM_Growth_Pct']].copy()
total_row = pd.DataFrame([{
    'Month': 'Total',
    'Department': 'All',
    'Expenditure': df['Expenditure'].sum(),
    'MoM_Growth_Pct': df['MoM_Growth_Pct'].dropna().mean().round(2)
}])
mom_summary = pd.concat([mom_summary, total_row], ignore_index=True)

print("\nMonthly Expenditure Summary (sample):")
print(mom_summary.tail(10).to_string(index=False))


# ── 2025 FORECAST ────────────────────────────────────────────
# Matches: 'Forecast 2025 Total by Department' bar chart

print("\n2025 Forecast (linear trend projection):")
forecast_rows = []
months_2025 = pd.date_range(start='2025-01-01', periods=12, freq='MS')

for dept in df['Department'].unique():
    dept_data = df[df['Department'] == dept].sort_values('Date')
    x = np.arange(len(dept_data))
    y = dept_data['Expenditure'].values
    slope, intercept = np.polyfit(x, y, 1)

    annual_forecast = 0
    for i, month in enumerate(months_2025):
        projected = intercept + slope * (len(dept_data) + i)
        projected = round(max(projected, 0), 2)
        annual_forecast += projected
        forecast_rows.append({
            'Date':        month,
            'Department':  dept,
            'Expenditure': round(projected, 2),
            'Budget':      round(projected * 1.05, 2),
            'Year':        2025,
            'Month':       month.strftime('%b %Y'),
            'Is_Forecast': True
        })

    print(f"  {dept}: ₹{round(annual_forecast, 1)}L projected for 2025")

df_forecast = pd.DataFrame(forecast_rows)

# Forecast chart
forecast_annual = df_forecast.groupby('Department')['Expenditure'].sum().round(1)

plt.figure(figsize=(7, 5))
bars = plt.barh(forecast_annual.index, forecast_annual.values, color=colors)
plt.title("2025 Forecast Total by Department (₹ Lakhs)", fontweight='bold')
plt.xlabel("Projected Expenditure (₹ Lakhs)")
for bar, val in zip(bars, forecast_annual.values):
    plt.text(val + 10, bar.get_y() + bar.get_height()/2,
             f"₹{val}L", va='center', fontsize=10, fontweight='bold')
plt.tight_layout()
plt.savefig("forecast_2025.png", dpi=120)
plt.show()


# ── EXPORT CLEAN DATASET FOR POWER BI ────────────────────────

# Tag actual data
df['Is_Forecast'] = False
df['Budget_Utilisation_Pct'] = (df['Expenditure'] / df['Budget'] * 100).round(2)

# Combine actual + forecast
df_final = pd.concat([df, df_forecast], ignore_index=True)
df_final = df_final.sort_values(['Department', 'Date']).reset_index(drop=True)

# Export
df_final.to_csv("hospital_clean_full.csv", index=False)
print(f"\nExported: hospital_clean_full.csv")
print(f"Final dataset: {df_final.shape[0]} rows × {df_final.shape[1]} columns")
print("→ Import this CSV into Power BI")
