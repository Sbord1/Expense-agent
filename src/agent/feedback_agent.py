import duckdb
from datetime import datetime
import uuid

DB_PATH = "data/expenses.duckdb"

def save_feedback(description: str, corrected_category: str):
    con = duckdb.connect(DB_PATH)

    con.execute("""
        INSERT INTO category_feedback
        VALUES (?, ?, ?, ?)
    """, [
        str(uuid.uuid4()),
        description.lower().strip(),
        corrected_category,
        datetime.utcnow()
    ])

    con.close()


def lookup_feedback(description: str):
    """
    Returns corrected_category if known, else None
    """
    con = duckdb.connect(DB_PATH)

    result = con.execute("""
        SELECT corrected_category
        FROM category_feedback
        WHERE description = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, [description.lower().strip()]).fetchone()

    con.close()

    if result:
        return result[0]

    return None