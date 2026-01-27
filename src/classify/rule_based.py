import duckdb

DB_PATH = "data/expenses.duckdb"

CATEGORIES = [
    "Food",
    "Transport",
    "Rent",
    "Subscriptions",
    "Utilities",
    "Shopping",
    "Leisure",
    "Other",
]

RULES = {
    "Subscriptions": [
        "spotify", "netflix", "prime", "amazon prime",
        "google", "apple", "icloud"
    ],
    "Transport": [
        "uber", "bolt", "tram", "metro", "bus", "taxi"
    ],
    "Food": [
        "restaurant", "ristorante", "bar", "cafe",
        "pizzeria", "mc", "burger"
    ],
    "Shopping": [
        "amazon", "zalando", "ikea"
    ],
    "Utilities": [
        "enel", "eni", "acea", "energia", "gas"
    ],
}

def apply_rules(description: str):
    """
    Returns:
        category (str)
        confidence (float)
    """
    if not description:
        return "Other", 0.0

    d = description.lower()

    for category, keywords in RULES.items():
        for kw in keywords:
            if kw in d:
                return category, 0.9

    # 👇 fallback FONDAMENTALE
    return "Other", 0.1


def main():
    con = duckdb.connect(DB_PATH)

    df = con.execute("""
        SELECT *
        FROM transactions_clean
    """).df()

    categories = []
    confidences = []

    for _, row in df.iterrows():
        cat, conf = apply_rules(row.get("description"))
        categories.append(cat)
        confidences.append(conf)

    df["category_rule"] = categories
    df["confidence_rule"] = confidences

    # Sovrascriviamo la tabella enriched
    con.execute("DROP TABLE IF EXISTS transactions_enriched")
    con.execute("""
        CREATE TABLE transactions_enriched AS
        SELECT * FROM df
    """)

    con.close()
    print("Rule-based categorization applied")


if __name__ == "__main__":
    main()