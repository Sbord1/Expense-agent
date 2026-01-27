import duckdb
import json
from openai import OpenAI

DB_PATH = "data/expenses.duckdb"
client = OpenAI()

def load_metrics():
    con = duckdb.connect(DB_PATH)

    monthly = con.execute("SELECT * FROM metrics_monthly").df()
    by_category = con.execute("SELECT * FROM metrics_by_category").df()
    trends = con.execute("SELECT * FROM metrics_trends").df()
    anomalies = con.execute("SELECT * FROM metrics_anomalies").df()

    con.close()

    return {
        "monthly": monthly.to_dict(orient="records"),
        "by_category": by_category.to_dict(orient="records"),
        "trends": trends.to_dict(orient="records"),
        "anomalies": anomalies.to_dict(orient="records"),
    }

def build_insight_prompt(metrics: dict) -> str:
    return f"""
        You are a personal finance insight agent.

        You receive aggregated financial metrics.
        Your task is to:
        - summarize spending behavior
        - highlight important changes
        - detect anomalies
        - give practical insights (not generic advice)

        Metrics (JSON):
        {json.dumps(metrics, indent=2)}

        Rules:
        - Be concise
        - Be specific
        - Reference numbers
        - No moral judgment
        - No generic budgeting advice

        Return your answer as bullet points.
        """

def generate_insights():
    metrics = load_metrics()
    prompt = build_insight_prompt(metrics)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    insights = generate_insights()
    print("\FINANCIAL INSIGHTS\n")
    print(insights)