import duckdb
import pandas as pd

DB_PATH = "data/expenses.duckdb"

con = duckdb.connect(DB_PATH)

# Carica raw
df = con.execute("""
    SELECT *
    FROM transactions_raw
""").df()

# Drop righe rotte
df = df.dropna(subset=["date", "amount", "description"])

# Normalizza stringhe
df["description"] = (
    df["description"]
    .str.strip()
    .str.lower()
)

if "merchant" in df.columns:
    df["merchant"] = (
        df["merchant"]
        .fillna("")
        .str.strip()
        .str.lower()
    )

# Deduplicazione
df = df.drop_duplicates(
    subset=["date", "amount", "description"]
)

# Feature temporali
df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.to_period("M").astype(str)
df["weekday"] = df["date"].dt.weekday
df["year"] = df["date"].dt.year

# ID stabile (importante per AI dopo)
df = df.reset_index(drop=True)
df["transaction_id"] = df.index.astype(str)

# Scrivi clean table
con.execute("DROP TABLE IF EXISTS transactions_clean")
con.execute("""
    CREATE TABLE transactions_clean AS
    SELECT * FROM df
""")

con.close()

print("Transactions_clean created successfully")