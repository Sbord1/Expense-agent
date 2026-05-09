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
from src.agent.feedback_agent import save_feedback

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
        SELECT transaction_id, description, amount, category_final, category_source, classification_debug, month
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
months_list = sorted(monthly["month"].unique())
selected_month_kpi = st.selectbox("Select month for KPIs", months_list, index=len(months_list)-1)

monthly_filtered = monthly[monthly["month"] == selected_month_kpi]

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Spent",
    f"€{monthly_filtered['total_spent'].iloc[0]:,.2f}"
)

col2.metric(
    "Avg Transaction",
    f"€{monthly_filtered['avg_transaction'].iloc[0]:,.2f}"
)

col3.metric(
    "Transactions",
    int(monthly_filtered['n_transactions'].iloc[0])
)

# New KPI: Top Category
top_cat = by_category[by_category["month"] == selected_month_kpi].sort_values("total_spent", ascending=False).iloc[0]["category_final"]
col4.metric(
    "Top Category",
    top_cat
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
    title="Monthly spending breakdown by category",
    text="total_spent"
)

fig_cat.update_traces(texttemplate='%{text:.2f}€', textposition='inside')

fig_cat.update_layout(
    yaxis_title="€ Spent",
    legend_title="Category"
)

st.plotly_chart(fig_cat)

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
    title=f"Trend for {selected_category}",
    text="total_spent"
)

fig_trend.update_traces(texttemplate='%{text:.2f}€', textposition='top center')

fig_trend.update_layout(
    yaxis_title="€ Spent",
    xaxis_title="Month"
)

st.plotly_chart(fig_trend)

st.divider()

# -------------------------------------------------
# Monthly Transaction View
# -------------------------------------------------
st.subheader("Monthly Transaction Details")

months = sorted(df["month"].dropna().unique()) if "month" in df.columns else []

if months:
    selected_month = st.selectbox("Select month", months)

    # Total spent for the month
    total_month = abs(df[(df["month"] == selected_month) & (df["amount"] < 0)]["amount"].sum())
    st.metric("Total Spent in Month", f"€{total_month:,.2f}")

    # Filter transactions for the selected month
    monthly_tx = df[df["month"] == selected_month]

    # Pie chart for category breakdown
    category_spend = monthly_tx.groupby("category_final")["amount"].sum().abs().reset_index()
    category_spend.columns = ["Category", "Spent"]

    fig_pie = px.pie(
        category_spend,
        values="Spent",
        names="Category",
        title=f"Category Breakdown for {selected_month}"
    )
    fig_pie.update_traces(textinfo='label+value', texttemplate='%{label}: %{value:.2f}€')
    st.plotly_chart(fig_pie)

    # Table of transactions
    st.subheader(f"Transactions for {selected_month}")
    monthly_tx = monthly_tx.copy()
    if "classification_debug" in monthly_tx.columns:
        monthly_tx["debug_summary"] = (
            monthly_tx["classification_debug"]
            .fillna("{}")
            .apply(lambda value: value[:120] + "..." if len(value) > 120 else value)
        )
    source_counts = (
        monthly_tx["category_source"]
        .fillna("unknown")
        .value_counts()
        .reset_index()
    )
    source_counts.columns = ["classification_source", "count"]
    st.subheader("Classification source breakdown")
    st.table(source_counts)
    st.dataframe(
        monthly_tx[["description", "amount", "category_final", "category_source", "debug_summary"]]
        .sort_values("amount"),
        width="stretch"
    )
else:
    st.write("No month data available.")
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
    desc = df.loc[df["transaction_id"] == tx_id, "description"].iloc[0]
    save_feedback(desc, new_cat)
    con = duckdb.connect(DB_PATH)
    con.execute(
        "UPDATE transactions_final SET category_final = ?, category_source = ?, confidence = ? WHERE transaction_id = ?",
        [new_cat, "feedback", 1.0, tx_id],
    )
    con.close()
    load_data.clear()
    st.success(
        f"Correction saved for transaction '{desc[:40]}...' as {new_cat}. Refresh the dashboard to see updated categories."
    )
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        st.rerun()

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