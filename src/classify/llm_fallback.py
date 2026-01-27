import duckdb
import json
import time
from typing import Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "data/expenses.duckdb"

CATEGORIES = [
    "Food",
    "Transport",
    "Rent",
    "Subscriptions",
    "Utilities",
    "Shopping",
    "Leisure",
    "Other"
]

# -----------------------
# LLM availability check
# -----------------------
try:
    client = OpenAI()
    LLM_AVAILABLE = True
except Exception:
    client = None
    LLM_AVAILABLE = False


def build_prompt(description: str, amount: float, categories: list[str]) -> str:
    return f"""
You are a personal finance classification agent.

Choose ONE category from this list:
{", ".join(categories)}

Transaction:
Description: "{description}"
Amount: {amount}

Return ONLY valid JSON in this format:
{{
  "category": "...",
  "confidence": 0.0-1.0,
  "reason": "very short explanation"
}}
"""


def classify_transaction_llm(
    description: str,
    amount: float,
    categories: list[str]
) -> Dict:
    """
    Returns:
    {
      "category": str,
      "confidence": float,
      "reason": str
    }
    """
    prompt = build_prompt(description, amount, categories)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "category": "Other",
            "confidence": 0.0,
            "reason": "invalid json from model"
        }


def run_llm_fallback():
    con = duckdb.connect(DB_PATH)

    # --------------------------------------------------
    # SAFETY NET: transactions_final ALWAYS exists
    # --------------------------------------------------
    con.execute("""
        CREATE OR REPLACE TABLE transactions_final AS
        SELECT
            *,
            category_rule AS category_final
        FROM transactions_enriched
    """)

    if not LLM_AVAILABLE:
        print("⚠️ OpenAI API key not found → skipping LLM fallback")
        con.close()
        return

    df = con.execute("""
        SELECT *
        FROM transactions_enriched
        WHERE category_rule IS NULL
    """).df()

    if df.empty:
        print("No transactions need LLM classification.")
        con.close()
        return

    categories_ai = []
    confidences_ai = []
    reasons_ai = []

    for _, row in df.iterrows():
        result = classify_transaction_llm(
            row["description"],
            row["amount"],
            CATEGORIES
        )

        categories_ai.append(result["category"])
        confidences_ai.append(result["confidence"])
        reasons_ai.append(result["reason"])

        time.sleep(0.3)  # rate limit safe

    df["category_ai"] = categories_ai
    df["confidence_ai"] = confidences_ai
    df["reason_ai"] = reasons_ai

    # --------------------------------------------------
    # Final merge
    # --------------------------------------------------
    con.execute("""
        CREATE OR REPLACE TABLE transactions_final AS
        SELECT
            e.*,
            f.category_ai,
            f.confidence_ai,
            f.reason_ai,
            COALESCE(e.category_rule, f.category_ai, 'Other') AS category_final
        FROM transactions_enriched e
        LEFT JOIN df f
        USING (transaction_id)
    """)

    con.close()
    print("LLM fallback classification completed")


if __name__ == "__main__":
    run_llm_fallback()