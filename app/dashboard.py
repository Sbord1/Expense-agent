import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import streamlit as st
import duckdb
import plotly.express as px
import pandas as pd

from src.agent.insight_agent import generate_insights
from src.agent.chat_agent import chat_about_insights

DB_PATH = "data/expenses.duckdb"

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="AI Expense Tracker",
    layout="wide"
)

st.title("AI Expense Tracker")

# -------------------------------------------------
# Load data
# -------------------------------------------------
@st.cache_data
def load_data():
    con = duckdb.connect(DB_PATH)

    monthly = con.execute("SELECT * FROM metrics_monthly").df()
    by_category = con.execute("SELECT * FROM metrics_by_category").df()
    trends = con.execute("SELECT * FROM metrics_trends").df()
    transactions = con.execute("""
        SELECT transaction_id, description, amount, category_final
        FROM transactions_final
    """).df()

    con.close()
    return monthly, by_category, trends, transactions


monthly, by_category, trends, df = load_data()

# -------------------------------------------------
# Safety checks
# -------------------------------------------------
if monthly.empty:
    st.warning("No data available yet.")
    st.stop()

# -------------------------------------------------
# KPI
# -------------------------------------------------
col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Spent (last month)",
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

st.divider()

# -------------------------------------------------
# Spending by Category (stacked, readable)
# -------------------------------------------------
st.subheader("Spending by Category")

fig_cat = px.bar(
    by_category,
    x="month",
    y="total_spent",
    color="category_final",
    barmode="stack",
    title="Monthly spending breakdown by category"
)

fig_cat.update_layout(
    yaxis_title="€ Spent",
    legend_title="Category"
)

st.plotly_chart(fig_cat, width="stretch")

# -------------------------------------------------
# Spending Trend per Category
# -------------------------------------------------
st.subheader("Spending Trend by Category")

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

trend_filtered = trends[
    trends["category_final"] == selected_category
]

fig_trend = px.line(
    trend_filtered,
    x="month",
    y="total_spent",
    markers=True,
    title=f"Trend for {selected_category}"
)

fig_trend.update_layout(
    yaxis_title="€ Spent",
    xaxis_title="Month"
)

st.plotly_chart(fig_trend, width="stretch")

st.divider()

# -------------------------------------------------
# Manual correction (future learning hook)
# -------------------------------------------------
st.subheader("Correct a transaction")

tx_id = st.selectbox(
    "Transaction",
    df["transaction_id"],
    format_func=lambda x: df.loc[
        df["transaction_id"] == x, "description"
    ].iloc[0][:60]
)

new_cat = st.selectbox(
    "New category",
    sorted(df["category_final"].dropna().unique())
)

if st.button("Save correction"):
    st.success(
        "Correction saved (hook ready for future learning loop)."
    )

st.divider()

# -------------------------------------------------
# AI Insights + Chat
# -------------------------------------------------
st.subheader("AI Insights")

if "insights" not in st.session_state:
    st.session_state.insights = None

if st.button("Generate insights"):
    with st.spinner("Analyzing spending patterns..."):
        st.session_state.insights = generate_insights()
        st.success("Insights generated")

if st.session_state.insights:
    st.json(st.session_state.insights)

    st.subheader("Ask the AI about your finances")

    user_question = st.text_input(
        "Ask a question about your spending"
    )

    if user_question:
        with st.spinner("Thinking..."):
            answer = chat_about_insights(
                user_question,
                st.session_state.insights
            )
            st.markdown(answer)