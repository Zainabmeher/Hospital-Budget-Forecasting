SQL queries - Hospital Budget Forecasting 

1. Total expenditure by department and year
SELECT
    Department,
    YEAR(`Date`) AS Year,
    SUM(Expenditure) AS Total_Expenditure
FROM hospital_budget
GROUP BY Department, YEAR(`Date`)
ORDER BY Year, Total_Expenditure DESC; 

2. Year-on-Year growth using SELF JOIN
WITH Yearly_Spend AS (
    SELECT
        Department,
        YEAR(`Date`) AS Year,
        SUM(Expenditure) AS Total_Expenditure
    FROM hospital_budget
    GROUP BY Department, YEAR(`Date`)
)
SELECT
    current.Department,
    current.Year,
    current.Total_Expenditure,
    previous.Total_Expenditure AS Previous_Year_Expenditure,
    ROUND(
        (current.Total_Expenditure - previous.Total_Expenditure)
        * 100.0 / previous.Total_Expenditure, 2
    ) AS YoY_Growth_Percentage
FROM Yearly_Spend current
LEFT JOIN Yearly_Spend previous
    ON current.Department = previous.Department
    AND current.Year = previous.Year + 1
ORDER BY current.Department, current.Year; 

3. Month-on-Month growth using LAG()
WITH Monthly_Spend AS (
    SELECT
        Department,
        YEAR(`Date`) AS Year,
        MONTH(`Date`) AS Month,
        SUM(Expenditure) AS Monthly_Expenditure
    FROM hospital_budget
    GROUP BY Department, YEAR(`Date`), MONTH(`Date`)
)
SELECT
    Department,
    Year,
    Month,
    Monthly_Expenditure,
    ROUND(
        (Monthly_Expenditure -
        LAG(Monthly_Expenditure) OVER (
            PARTITION BY Department
            ORDER BY Year, Month
        ))
        * 100.0 /
        LAG(Monthly_Expenditure) OVER (
            PARTITION BY Department
            ORDER BY Year, Month
        ), 2
    ) AS MoM_Growth_Percentage
FROM Monthly_Spend
ORDER BY Department, Year, Month; 

4. Running total by department
SELECT
    Department,
    `Date`,
    Expenditure,
    SUM(Expenditure) OVER (
        PARTITION BY Department
        ORDER BY `Date`
    ) AS Running_Total
FROM hospital_budget
ORDER BY Department, `Date`; 

5. Department contribution % of total expenditure
SELECT
    Department,
    SUM(Expenditure) AS Department_Expenditure,
    ROUND(
        SUM(Expenditure) * 100.0 /
        SUM(SUM(Expenditure)) OVER (), 2
    ) AS Contribution_Percentage
FROM hospital_budget
GROUP BY Department
ORDER BY Department_Expenditure DESC; 

6. Budget status classification
SELECT
    Department,
    YEAR(`Date`) AS Year,
    SUM(Expenditure) AS Total_Expenditure,
    SUM(Budget) AS Total_Budget,
    CASE
        WHEN SUM(Expenditure) > SUM(Budget) THEN 'Over Budget'
        WHEN SUM(Expenditure) = SUM(Budget) THEN 'On Budget'
        ELSE 'Under Budget'
    END AS Budget_Status
FROM hospital_budget
GROUP BY Department, YEAR(`Date`)
ORDER BY Year, Department; 

7. Department spend ranking
SELECT
    Department,
    SUM(Expenditure) AS Total_Expenditure,
    RANK() OVER (
        ORDER BY SUM(Expenditure) DESC
    ) AS Spend_Rank
FROM hospital_budget
GROUP BY Department
ORDER BY Spend_Rank;