import duckdb

DB_PATH = "data/expenses.duckdb"

con = duckdb.connect(DB_PATH)

con.execute("""
CREATE OR REPLACE TABLE metrics_monthly AS
SELECT
    month,
    COUNT(*) AS n_transactions,
    SUM(amount) AS total_spent,
    AVG(amount) AS avg_transaction
FROM transactions_final
GROUP BY month
ORDER BY month
""")

con.execute("""
CREATE OR REPLACE TABLE metrics_by_category AS
SELECT
    month,
    category_final,
    COUNT(*) AS n_transactions,
    SUM(amount) AS total_spent,
    AVG(amount) AS avg_transaction
FROM transactions_final
GROUP BY month, category_final
ORDER BY month, total_spent DESC
""")

con.execute("""
CREATE OR REPLACE TABLE metrics_trends AS
SELECT
    category_final,
    month,
    SUM(amount) AS total_spent,
    SUM(amount)
      - LAG(SUM(amount)) OVER (
            PARTITION BY category_final
            ORDER BY month
        ) AS delta_vs_prev_month
FROM transactions_final
GROUP BY category_final, month
ORDER BY category_final, month
""")


con.execute("""
CREATE OR REPLACE TABLE metrics_anomalies AS
SELECT
    category_final,
    month,
    total_spent,
    CASE
        WHEN total_spent > 1.3 * AVG(total_spent)
            OVER (PARTITION BY category_final)
        THEN 1
        ELSE 0
    END AS is_anomaly
FROM metrics_trends
""")

con.close()
print("Metrics tables created")