import pandas as pd
import duckdb

CSV_PATH = "data/revolut.csv"
DB_PATH = "data/expenses.duckdb"

df = pd.read_csv(CSV_PATH, sep=';')

df = df.rename(columns={
    "Data di completamento": "date",
    "Descrizione": "description",
    "Importo": "amount",
    "Valuta": "currency"
})

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

con = duckdb.connect(DB_PATH)

con.execute("""
CREATE TABLE IF NOT EXISTS transactions_raw AS
SELECT * FROM df
""")

con.close()



print("Revolut CSV ingested successfully")