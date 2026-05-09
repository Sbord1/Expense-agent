import duckdb
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from src.agent.orchestrator import ClassificationOrchestrator

DB_PATH = "data/expenses.duckdb"

orchestrator = ClassificationOrchestrator()

con = duckdb.connect(DB_PATH)

df = con.execute("SELECT * FROM transactions_clean").df()

categories = []
sources = []
confidences = []
debugs = []

for _, row in df.iterrows():
    result = orchestrator.classify(
        row["description"],
        row["amount"]
        , row["transaction_id"]
    )

    categories.append(result["category"])
    sources.append(result["source"])
    confidences.append(result["confidence"])
    debugs.append(json.dumps(result.get("debug", {})))

df["category_final"] = categories
df["category_source"] = sources
df["confidence"] = confidences
df["classification_debug"] = debugs

con.execute("DROP TABLE IF EXISTS transactions_final")
con.execute("""
    CREATE TABLE transactions_final AS
    SELECT * FROM df
""")

con.close()

print("Classification completed via orchestrator")