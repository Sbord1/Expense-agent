import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import streamlit as st
import duckdb
import plotly.express as px
from src.agent.insight_agent import generate_insights

DB_PATH = "data/expenses.duckdb"

st.set_page_config(
    page_title="AI Expense Tracker",
    layout="wide"
)

st.title("AI Expense Tracker")

# ---------------------------
# Load data
# ---------------------------
@st.cache_data
def load_data():
    con = duckdb.connect(DB_PATH)

    monthly = con.execute("SELECT * FROM metrics_monthly").df()
    by_category = con.execute("SELECT * FROM metrics_by_category").df()
    trends = con.execute("SELECT * FROM metrics_trends").df()

    con.close()
    return monthly, by_category, trends


monthly, by_category, trends = load_data()

# ---------------------------
# Safety checks 
# ---------------------------
if monthly.empty:
    st.warning("No data available yet.")
    st.stop()

# ---------------------------
# KPI
# ---------------------------
col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Spent",
    f"€{monthly['total_spent'].iloc[-1]:,.2f}"
)

col2.metric(
    "Avg Transaction",
    f"€{monthly['avg_transaction'].iloc[-1]:,.2f}"
)

col3.metric(
    "Transactions",
    int(monthly['n_transactions'].iloc[-1])
)

# ---------------------------
# Spending by Category
# ---------------------------
st.subheader("Spending by Category")

fig_cat = px.bar(
    by_category,
    x="category_final",
    y="total_spent",
    color="month",
    text_auto=".2s"
)

st.plotly_chart(fig_cat, use_container_width=True)

# ---------------------------
# Spending Trend (per category)
# ---------------------------
st.subheader("Spending Trend")

categories = (
    trends["category_final"]
    .dropna()
    .astype(str)
    .unique()
)

selected_category = st.selectbox(
    "Select category",
    sorted(categories)
)

trend_filtered = trends[trends["category_final"] == selected_category]

fig_trend = px.line(
    trend_filtered,
    x="month",
    y="total_spent",
    markers=True
)

st.plotly_chart(fig_trend, use_container_width=True)

# ---------------------------
# AI Insights 
# ---------------------------
st.subheader("AI Insights")

try:
    if st.button("Generate insights"):
        with st.spinner("Thinking..."):
            insights = generate_insights()
            st.markdown(insights)
except Exception:
    st.info("AI insights unavailable on this machine.")