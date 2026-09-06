# ============================================================
# HOSPITAL EXPENDITURE ANALYSIS & BUDGET FORECASTING
# Python Pipeline Script — Run this AFTER SQL
# ============================================================
# HOW TO RUN:
# 1. Open Jupyter Notebook (via Anaconda Navigator)
# 2. Copy-paste each section into separate cells
# 3. Run each cell with Shift + Enter
# OR: Open terminal, navigate to this folder, run:
#     python hospital_pipeline.py
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ── Set clean plot style ──────────────────────────────────────
plt.rcParams.update({
    'figure.facecolor': '#F0F4F8',
    'axes.facecolor':   '#FFFFFF',
    'axes.grid':        True,
    'grid.color':       '#E2EAF0',
    'grid.linewidth':   0.6,
    'font.family':      'sans-serif',
    'axes.spines.top':  False,
    'axes.spines.right':False,
})

DEPT_COLOURS = {
    'Icu':           '#1B6CA8',
    'Radiology':    '#F59E0B',
    'General Ward': '#22C55E'
}

# ============================================================
# SECTION 1 — LOAD & INSPECT
# ============================================================
print("=" * 55)
print("SECTION 1: Loading data")
print("=" * 55)

# ── Change this path to wherever your Excel file is saved ──
FILE_PATH = "Budget_Forecasting_Dataset.xlsx"

df = pd.read_excel(FILE_PATH)

print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nFirst 5 rows:\n{df.head()}")
print(f"\nData types:\n{df.dtypes}")
print(f"\nNull values:\n{df.isnull().sum()}")
print(f"\nDepartments: {df['Department'].unique()}")
print(f"Years: {df['Year'].unique()}")
print(f"Date range: {df['Date'].min()} → {df['Date'].max()}")


# ============================================================
# SECTION 2 — DATA CLEANING
# ============================================================
print("\n" + "=" * 55)
print("SECTION 2: Cleaning")
print("=" * 55)

# Fix date column
df['Date'] = pd.to_datetime(df['Date'])

# Standardise department names (strip whitespace, consistent caps)
df['Department'] = df['Department'].str.strip().str.title()

# Add month name and month number for easier analysis
df['Month']      = df['Date'].dt.strftime('%b %Y')        # e.g. "Jan 2023"
df['Month_Num']  = df['Date'].dt.month                    # 1–12
df['Month_Name'] = df['Date'].dt.strftime('%b')           # e.g. "Jan"

# Drop duplicates if any
before = len(df)
df = df.drop_duplicates()
print(f"Duplicates removed: {before - len(df)}")
print(f"Nulls after clean: {df.isnull().sum().sum()}")
print("Cleaning complete ✓")


# ============================================================
# SECTION 3 — FEATURE ENGINEERING
# ============================================================
# Creating new columns the raw data doesn't have
# These are what Power BI will use for its visuals
print("\n" + "=" * 55)
print("SECTION 3: Feature engineering")
print("=" * 55)

# ── 3a. Synthetic Budget column ───────────────────────────────
# NOTE: Our dataset has only Expenditure — no Budget column.
# We simulate a realistic budget using historical overspend patterns:
# ICU runs ~10% over, Radiology ~8% over, General Ward ~6% over.
# This mirrors real hospital operations where ICU is hardest to budget.
# Document this in your README exactly as explained.

np.random.seed(42)
BUDGET_FACTORS = {
    'Icu':           {'2023': 0.90, '2024': 0.88},   # ICU always overspends
    'Radiology':    {'2023': 0.93, '2024': 0.91},
    'General Ward': {'2023': 0.95, '2024': 0.93}
}

budgets = []
for _, row in df.iterrows():
    dept = row['Department']
    year = str(row['Year'])
    base = BUDGET_FACTORS.get(dept, {}).get(year, 0.92)
    noise = np.random.uniform(-0.03, 0.03)
    budgets.append(round(row['Expenditure'] * (base + noise), 2))

df['Budget'] = budgets

# ── 3b. Variance columns ─────────────────────────────────────
df['Variance']     = (df['Expenditure'] - df['Budget']).round(2)
df['Variance_Pct'] = ((df['Variance'] / df['Budget']) * 100).round(2)

# ── 3c. Budget status label (like CASE WHEN in SQL) ──────────
def budget_status(pct):
    if pct > 8:
        return 'Over Budget'
    elif pct < -5:
        return 'Under Budget'
    else:
        return 'On Track'

df['Budget_Status'] = df['Variance_Pct'].apply(budget_status)

# ── 3d. Month-on-Month growth % ──────────────────────────────
df = df.sort_values(['Department', 'Date']).reset_index(drop=True)
df['Prev_Month_Spend'] = df.groupby('Department')['Expenditure'].shift(1)
df['MoM_Growth_Pct']   = (
    (df['Expenditure'] - df['Prev_Month_Spend'])
    / df['Prev_Month_Spend'] * 100
).round(2)

# ── 3e. Running total per department ─────────────────────────
df['Running_Total'] = df.groupby('Department')['Expenditure'].cumsum()

# ── 3f. Budget Utilisation % ─────────────────────────────────
df['Budget_Utilisation_Pct'] = (
    df['Expenditure'] / df['Budget'] * 100
).round(2)

print("New columns created:")
new_cols = ['Budget','Variance','Variance_Pct','Budget_Status',
            'MoM_Growth_Pct','Running_Total','Budget_Utilisation_Pct']
for c in new_cols:
    print(f"  ✓ {c}")

print(f"\nSample enriched data:\n{df[['Date','Department','Expenditure','Budget','Variance_Pct','Budget_Status']].head(6)}")


# ============================================================
# SECTION 4 — EXPLORATORY DATA ANALYSIS (EDA)
# ============================================================
print("\n" + "=" * 55)
print("SECTION 4: EDA")
print("=" * 55)

# ── 4a. Summary statistics ────────────────────────────────────
print("\nDescriptive stats — Expenditure by Department:")
print(df.groupby('Department')['Expenditure'].describe().round(2))

# ── 4b. YoY growth ───────────────────────────────────────────
print("\nYear-on-Year growth:")
yearly = df.groupby(['Department','Year'])['Expenditure'].sum().reset_index()
for dept in df['Department'].unique():
    d = yearly[yearly['Department']==dept]
    if len(d) == 2:
        growth = (d.iloc[1]['Expenditure'] - d.iloc[0]['Expenditure']) / d.iloc[0]['Expenditure'] * 100
        print(f"  {dept}: {growth:.1f}% YoY growth (2023→2024)")

# ── 4c. Department share of total spend ───────────────────────
print("\nDept share of total expenditure:")
total = df['Expenditure'].sum()
for dept in df['Department'].unique():
    dept_total = df[df['Department']==dept]['Expenditure'].sum()
    print(f"  {dept}: ₹{dept_total}L ({dept_total/total*100:.1f}%)")

# ── 4d. Budget status breakdown ───────────────────────────────
print("\nBudget status count by department:")
print(df.groupby(['Department','Budget_Status']).size().unstack(fill_value=0))


# ── CHARTS ───────────────────────────────────────────────────

# Chart 1: Expenditure trend per department (line chart)
fig, axes = plt.subplots(2, 2, figsize=(14, 9))
fig.suptitle('Hospital Expenditure EDA — 2023–2024', fontsize=14, fontweight='600', color='#1A2332', y=1.01)

ax1 = axes[0, 0]
for dept, colour in DEPT_COLOURS.items():
    d = df[df['Department']==dept].sort_values('Date')
    ax1.plot(d['Date'], d['Expenditure'], marker='o', markersize=3,
             color=colour, linewidth=2, label=dept)
ax1.set_title('Monthly Expenditure Trend', fontweight='600', color='#1A2332')
ax1.set_xlabel('')
ax1.set_ylabel('Expenditure (₹ Lakhs)')
ax1.legend(frameon=False)
ax1.tick_params(axis='x', rotation=30)

# Chart 2: Total by dept per year (grouped bar)
ax2 = axes[0, 1]
yearly_pivot = yearly.pivot(index='Department', columns='Year', values='Expenditure')
x = np.arange(len(yearly_pivot))
width = 0.35
bars1 = ax2.bar(x - width/2, yearly_pivot[2023], width, label='2023',
                color=[DEPT_COLOURS[d] for d in yearly_pivot.index], alpha=0.6)
bars2 = ax2.bar(x + width/2, yearly_pivot[2024], width, label='2024',
                color=[DEPT_COLOURS[d] for d in yearly_pivot.index], alpha=1.0)
ax2.set_xticks(x)
ax2.set_xticklabels(yearly_pivot.index, fontsize=10)
ax2.set_title('Total Spend: 2023 vs 2024', fontweight='600', color='#1A2332')
ax2.set_ylabel('Expenditure (₹ Lakhs)')
ax2.legend(frameon=False)

# Chart 3: Variance % distribution (histogram)
ax3 = axes[1, 0]
for dept, colour in DEPT_COLOURS.items():
    d = df[df['Department']==dept]['Variance_Pct'].dropna()
    ax3.hist(d, bins=10, alpha=0.6, color=colour, label=dept, edgecolor='white')
ax3.axvline(x=0, color='#1A2332', linewidth=1, linestyle='--', label='Break-even')
ax3.set_title('Budget Variance % Distribution', fontweight='600', color='#1A2332')
ax3.set_xlabel('Variance %')
ax3.set_ylabel('Frequency')
ax3.legend(frameon=False)

# Chart 4: MoM Growth over time
ax4 = axes[1, 1]
for dept, colour in DEPT_COLOURS.items():
    d = df[df['Department']==dept].dropna(subset=['MoM_Growth_Pct']).sort_values('Date')
    ax4.plot(d['Date'], d['MoM_Growth_Pct'], marker='s', markersize=3,
             color=colour, linewidth=1.5, label=dept)
ax4.axhline(y=0, color='#8A9BB0', linewidth=0.8, linestyle='--')
ax4.set_title('Month-on-Month Growth %', fontweight='600', color='#1A2332')
ax4.set_xlabel('')
ax4.set_ylabel('MoM Growth %')
ax4.legend(frameon=False)
ax4.tick_params(axis='x', rotation=30)

plt.tight_layout()
plt.savefig('eda_charts.png', dpi=150, bbox_inches='tight')
plt.show()
print("EDA chart saved as eda_charts.png ✓")


# ============================================================
# SECTION 5 — FORECASTING (2025)
# ============================================================
print("\n" + "=" * 55)
print("SECTION 5: 2025 Forecast")
print("=" * 55)

# Method: Linear trend extrapolation using last 6 months
# Why: Simple, transparent, and defensible for a portfolio project
# Document this in your README

forecast_rows = []
months_2025 = pd.date_range(start='2025-01-01', periods=12, freq='MS')

for dept in df['Department'].unique():
    dept_data = df[df['Department'] == dept].sort_values('Date')

    # Fit linear trend on last 12 months of actual data
    last_12 = dept_data.tail(12).reset_index(drop=True)
    x = np.arange(len(last_12))
    y = last_12['Expenditure'].values
    slope, intercept = np.polyfit(x, y, 1)

    # Project 12 months forward
    for i, month in enumerate(months_2025):
        forecast_spend = intercept + slope * (len(last_12) + i)
        forecast_spend = round(max(forecast_spend, 0), 2)

        # Budget for 2025: 5% above forecast (planning buffer)
        forecast_budget = round(forecast_spend * 1.05, 2)

        forecast_rows.append({
            'Date':            month,
            'Department':      dept,
            'Expenditure':     forecast_spend,
            'Budget':          forecast_budget,
            'Variance':        round(forecast_spend - forecast_budget, 2),
            'Variance_Pct':    round((forecast_spend - forecast_budget) / forecast_budget * 100, 2),
            'Budget_Status':   'Forecast',
            'Month':           month.strftime('%b %Y'),
            'Month_Num':       month.month,
            'Month_Name':      month.strftime('%b'),
            'Year':            2025,
            'MoM_Growth_Pct':  round(slope / y[-1] * 100, 2),
            'Running_Total':   0,   # will update below
            'Budget_Utilisation_Pct': round(forecast_spend / forecast_budget * 100, 2),
            'Prev_Month_Spend': None,
            'Is_Forecast':     True
        })
        print(f"  {dept} {month.strftime('%b %Y')}: ₹{forecast_spend:.1f}L (budget ₹{forecast_budget:.1f}L)")

df_forecast = pd.DataFrame(forecast_rows)

# Annual forecast summary
print("\n2025 Forecast Summary:")
annual = df_forecast.groupby('Department')['Expenditure'].sum()
for dept, total in annual.items():
    print(f"  {dept}: ₹{total:.1f}L")
print(f"  TOTAL: ₹{annual.sum():.1f}L")


# ============================================================
# SECTION 6 — COMBINE & EXPORT
# ============================================================
print("\n" + "=" * 55)
print("SECTION 6: Export")
print("=" * 55)

# Tag actual data
df['Is_Forecast'] = False

# Add Is_Forecast column to forecast df already done above
# Combine
df_final = pd.concat([df, df_forecast], ignore_index=True)
df_final = df_final.sort_values(['Department', 'Date']).reset_index(drop=True)

# Recalculate running total including forecast
df_final['Running_Total'] = df_final.groupby('Department')['Expenditure'].cumsum().round(2)

print(f"Final dataset shape: {df_final.shape}")
print(f"Years in data: {sorted(df_final['Year'].unique())}")
print(f"\nColumn list for Power BI:\n{df_final.columns.tolist()}")

# Export 1: Full dataset (actual + forecast) for Power BI
df_final.to_csv('hospital_clean_full.csv', index=False)
print("\n✓ Exported: hospital_clean_full.csv  ← IMPORT THIS INTO POWER BI")

# Export 2: Actual only (2023–2024)
df[df['Year'].isin([2023, 2024])].to_csv('hospital_actual_only.csv', index=False)
print("✓ Exported: hospital_actual_only.csv")

# Export 3: Forecast only (2025)
df_forecast.to_csv('hospital_forecast_2025.csv', index=False)
print("✓ Exported: hospital_forecast_2025.csv")

# Export 4: Annual summary table
annual_summary = df_final.groupby(['Department', 'Year']).agg(
    Total_Expenditure=('Expenditure', 'sum'),
    Total_Budget=('Budget', 'sum'),
    Total_Variance=('Variance', 'sum'),
    Avg_Variance_Pct=('Variance_Pct', 'mean'),
    Avg_MoM_Growth=('MoM_Growth_Pct', 'mean')
).round(2).reset_index()
annual_summary.to_csv('hospital_annual_summary.csv', index=False)
print("✓ Exported: hospital_annual_summary.csv")

print("\n" + "=" * 55)
print("PIPELINE COMPLETE ✓")
print("=" * 55)
print("Next step: Open Power BI → Get Data → CSV")
print("Import:    hospital_clean_full.csv")
print("=" * 55)


# ============================================================
# SECTION 7 — FORECAST CHART (for EDA notebook)
# ============================================================

fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=False)
fig.suptitle('2025 Budget Forecast by Department', fontsize=13, fontweight='600', color='#1A2332')

for ax, dept in zip(axes, df['Department'].unique()):
    colour = DEPT_COLOURS.get(dept, '#555')

    actual = df[df['Department'] == dept].sort_values('Date')
    forecast = df_forecast[df_forecast['Department'] == dept].sort_values('Date')

    # Actual line
    ax.plot(actual['Date'], actual['Expenditure'],
            color=colour, linewidth=2, marker='o', markersize=3, label='Actual')

    # Forecast line (dashed)
    ax.plot(forecast['Date'], forecast['Expenditure'],
            color=colour, linewidth=2, linestyle='--', marker='s', markersize=3,
            alpha=0.7, label='Forecast')

    # Forecast budget line
    ax.plot(forecast['Date'], forecast['Budget'],
            color='#8A9BB0', linewidth=1.2, linestyle=':', label='Budget 2025')

    # Shade forecast zone
    ax.axvspan(forecast['Date'].min(), forecast['Date'].max(),
               alpha=0.06, color=colour)

    ax.set_title(dept, fontweight='600', color='#1A2332')
    ax.set_xlabel('')
    ax.set_ylabel('₹ Lakhs')
    ax.tick_params(axis='x', rotation=35)
    ax.legend(frameon=False, fontsize=8)

plt.tight_layout()
plt.savefig('forecast_chart.png', dpi=150, bbox_inches='tight')
plt.show()
print("Forecast chart saved as forecast_chart.png ✓")
