import duckdb
from src.agent.orchestrator import ClassificationOrchestrator

DB_PATH = "data/expenses.duckdb"

orchestrator = ClassificationOrchestrator()

con = duckdb.connect(DB_PATH)

df = con.execute("SELECT * FROM transactions_clean").df()

categories = []
sources = []
confidences = []

for _, row in df.iterrows():
    result = orchestrator.classify(
        row["description"],
        row["amount"]
    )

    categories.append(result["category"])
    sources.append(result["source"])
    confidences.append(result["confidence"])

df["category_final"] = categories
df["category_source"] = sources
df["confidence"] = confidences

con.execute("DROP TABLE IF EXISTS transactions_final")
con.execute("""
    CREATE TABLE transactions_final AS
    SELECT * FROM df
""")

con.close()

print("Classification completed via orchestrator")