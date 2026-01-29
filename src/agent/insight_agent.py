import duckdb
import pandas as pd
from typing import List, Dict, Any

DB_PATH = "data/expenses.duckdb"


# =========================
# Insight Agent (deterministico)
# =========================

def generate_insights() -> List[Dict[str, Any]]:
    """
    Returns a list of structured insights.
    No LLM usage here.
    """
    con = duckdb.connect(DB_PATH)

    df = con.execute("""
        SELECT
            date,
            month,
            category_final,
            amount
        FROM transactions_final
    """).df()

    con.close()

    if df.empty:
        return []

    insights = []

    insights += detect_monthly_spike(df)
    insights += detect_category_outliers(df)
    insights += detect_recurring_high_spend(df)

    return insights


# =========================
# INSIGHT 1: Monthly spike
# =========================

def detect_monthly_spike(df: pd.DataFrame) -> List[Dict[str, Any]]:
    monthly = (
        df.groupby("month")["amount"]
        .sum()
        .reset_index()
        .sort_values("month")
    )

    if len(monthly) < 3:
        return []

    last = monthly.iloc[-1]
    prev_avg = monthly.iloc[:-1]["amount"].mean()

    if last["amount"] > prev_avg * 1.3:
        return [{
            "type": "monthly_spike",
            "severity": "high",
            "month": last["month"],
            "value": float(last["amount"]),
            "baseline": float(prev_avg),
            "message": "Spending significantly higher than usual this month"
        }]

    return []


# =========================
# INSIGHT 2: Category outliers
# =========================

def detect_category_outliers(df: pd.DataFrame) -> List[Dict[str, Any]]:
    insights = []

    grouped = (
        df.groupby(["month", "category_final"])["amount"]
        .sum()
        .reset_index()
    )

    for category in grouped["category_final"].unique():
        cat_df = grouped[grouped["category_final"] == category]

        if len(cat_df) < 3:
            continue

        avg = cat_df["amount"].mean()
        last = cat_df.iloc[-1]

        if last["amount"] > avg * 1.5:
            insights.append({
                "type": "category_outlier",
                "severity": "medium",
                "category": category,
                "month": last["month"],
                "value": float(last["amount"]),
                "baseline": float(avg),
                "message": f"Unusual spending increase in {category}"
            })

    return insights


# =========================
# INSIGHT 3: Recurring high spend
# =========================

def detect_recurring_high_spend(df: pd.DataFrame) -> List[Dict[str, Any]]:
    insights = []

    recurring = (
        df.groupby(["category_final", "month"])["amount"]
        .sum()
        .reset_index()
    )

    counts = (
        recurring.groupby("category_final")["month"]
        .count()
        .reset_index(name="months_active")
    )

    for _, row in counts.iterrows():
        if row["months_active"] >= 4:
            insights.append({
                "type": "recurring_spend",
                "severity": "low",
                "category": row["category_final"],
                "months_active": int(row["months_active"]),
                "message": "Recurring spending detected over multiple months"
            })

    return insights