import duckdb
import json
from openai import OpenAI

DB_PATH = "data/expenses.duckdb"
client = OpenAI()

def run_sql(query: str):
    con = duckdb.connect(DB_PATH)
    try:
        df = con.execute(query).df()
    except Exception as e:
        df = None
        error = str(e)
    else:
        error = None
    con.close()
    return df, error

def build_sql_prompt(user_question: str) -> str:
    return f"""
        You are a data analyst agent.

        Your task:
        - Translate the user question into ONE valid SQL query.
        - The database is DuckDB.
        - Available tables:
            - transactions_final
            - metrics_monthly
            - metrics_by_category
            - metrics_trends
            - metrics_anomalies

        Rules:
            - Use ONLY SELECT queries
            - No data modification
            - Be concise
            - Return ONLY valid SQL, nothing else

        User question:
        "{user_question}"
        """

def generate_sql(user_question: str) -> str:
    prompt = build_sql_prompt(user_question)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()


def build_answer_prompt(question: str, sql: str, data: list[dict]) -> str:
    return f"""
        You are a personal finance assistant.

        User question:
        {question}

        SQL executed:
        {sql}

        Query result (JSON):
        {json.dumps(data, indent=2)}

        Explain the result clearly and concisely.
        Reference numbers.
        No assumptions beyond the data.
        """

    def generate_answer(question: str, sql: str, df):
        data = df.to_dict(orient="records")

        prompt = build_answer_prompt(question, sql, data)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        return response.choices[0].message.content
    
    def ask_finances(question: str):
        sql = generate_sql(question)
        df, error = run_sql(sql)

        if error:
            return f"SQL Error: {error}"

        if df.empty:
            return "No data found for this question."

        answer = generate_answer(question, sql, df)
        return answer

    if __name__ == "__main__":
    while True:
        q = input("\nAsk about your finances: ")
        if q.lower() in {"exit", "quit"}:
            break
        print("\n", ask_finances(q))