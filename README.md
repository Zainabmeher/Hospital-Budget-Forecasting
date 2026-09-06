# Hospital-Budget-Forecasting

End-to-end hospital expenditure analysis and 2025 budget forecast - SQL, Python, Power BI 

#Business Problem

A hospital network had 2 years of departmental expenditure data across ICU, Radiology, and General Ward but no structured budget tracking, no variance analysis, and no forward-looking forecast. Leadership needed to understand where money was going, which departments were at risk, and how to plan the 2025 budget.

Core questions this project answers:

-Which departments are growing fastest and why?

-What does the 2025 expenditure look like if current trends continue?

-Where should leadership focus cost control efforts?

#Tools & Technologies 

-Data Extraction - SQL; YoY growth, MoM trends, window functions, spend rankings

-Data Processing - Python (pandas, matplotlib); Cleaning, feature engineering, forecasting model

-Visualisation - Power BI; 3-page executive dashboard

-AI Integration - AI-assisted analysis; Insight generation, recommendation structuring 

#Pipeline Architecture 

Raw Dataset (Excel - 72 rows, 3 departments, 2 years)
    ↓
SQL - exploration, YoY growth, MoM trends, window functions
    ↓
Python - cleaning, budget simulation, variance engineering,
          12-month linear trend forecast
    ↓
Enriched Dataset (108 rows, 16 columns - exported CSV)
    ↓
Power BI - 3-page dashboard
    ↓
Business Recommendations + Action Plan 

#Python

The raw dataset had only 4 columns (Date, Department, Expenditure, Year). Python was used to engineered 12 additional columns:

-Budget - Simulated planned budget based on historical overspend patterns

-Variance - Actual spend minus planned budget

-Variance_Pct - Variance as a percentage of budget

-Budget_Status - Over Budget / On Track / Under Budget classification

-MoM_Growth_Pct - Month-on-month expenditure growth percentage

-Running_Total - Cumulative spend per department

-Budget_Utilisation_Pct - Actual as % of budget

-Forecast (2025) - 12-month projection using linear trend graph

*Note on budget simulation: The original dataset contained expenditure data only - no planned budget column. A synthetic budget was generated using department-specific overspend factors (ICU: 10% over, Radiology: 8% over, General Ward: 6% over) based on real-world hospital cost patterns. This is documented transparently as a data engineering decision. 

#SQL Queries

-Total expenditure by department and year

-Year-on-Year growth calculation using self-JOIN

-Month-on-Month growth using LAG() window function

-Running total using SUM() OVER (PARTITION BY)

-Department contribution % of total spend

-Budget status classification using CASE WHEN

-Spend ranking using RANK() window function

#Key Findings

- ICU is the highest-cost department at 46% of total expenditure with 35.2% YoY growth - highest risk
  
- Radiology showed 40.7% YoY growth - driven by equipment and maintenance costs
  
- General Ward has the most controlled growth at 18.6% YoY - best benchmark for cost practices
  
- All 3 departments show consistent linear growth with no seasonal dips - indicating structural cost inflation
  
- November–December 2024 ICU spike (MoM growth 3.5%) signals an emerging cost control issue






