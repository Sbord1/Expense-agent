import os
import json
import math
import difflib
import duckdb
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from src.agent.base import Agent

DB_PATH = "data/expenses.duckdb"
EMBEDDING_MODEL = "text-embedding-3-small"


class EmbeddingSimilarityAgent(Agent):
    name = "embedding_similarity"

    def __init__(self):
        self.client = OpenAI() if OpenAI and os.getenv("OPENAI_API_KEY") else None
        self._ensure_table()

    def _ensure_table(self):
        con = duckdb.connect(DB_PATH)
        con.execute("""
            CREATE TABLE IF NOT EXISTS classification_memory (
                transaction_id TEXT PRIMARY KEY,
                description TEXT,
                category TEXT,
                embedding TEXT,
                created_at TIMESTAMP
            )
        """)
        con.close()

    def _create_embedding(self, text: str) -> Optional[List[float]]:
        if self.client is None:
            return None

        resp = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        return resp.data[0].embedding

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def _string_similarity(a: str, b: str) -> float:
        return difflib.SequenceMatcher(None, a, b).ratio()

    def load_memory(self) -> List[Dict[str, Any]]:
        con = duckdb.connect(DB_PATH)
        rows = con.execute(
            "SELECT transaction_id, description, category, embedding FROM classification_memory"
        ).fetchall()
        con.close()

        memory = []
        for txn_id, description, category, embedding_json in rows:
            embedding = json.loads(embedding_json) if embedding_json else None
            memory.append({
                "transaction_id": txn_id,
                "description": description,
                "category": category,
                "embedding": embedding,
            })
        return memory

    def upsert_memory(self, transaction_id: str, description: str, category: str):
        embedding = self._create_embedding(description) if self.client else None
        con = duckdb.connect(DB_PATH)
        con.execute(
            "DELETE FROM classification_memory WHERE transaction_id = ?",
            [transaction_id],
        )
        con.execute(
            "INSERT INTO classification_memory VALUES (?, ?, ?, ?, ?)",
            [
                transaction_id,
                description,
                category,
                json.dumps(embedding) if embedding is not None else json.dumps([]),
                datetime.utcnow(),
            ],
        )
        con.close()

    def find_similar(self, description: str, top_n: int = 3) -> List[Dict[str, Any]]:
        memory = self.load_memory()
        query_embedding = self._create_embedding(description) if self.client else None

        scored = []
        for item in memory:
            if query_embedding is not None and item["embedding"]:
                score = self._cosine_similarity(query_embedding, item["embedding"])
            else:
                score = self._string_similarity(description, item["description"])
            scored.append({
                "transaction_id": item["transaction_id"],
                "description": item["description"],
                "category": item["category"],
                "score": score,
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_n]

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        description = input.get("description", "").lower().strip()
        matches = self.find_similar(description)

        if not matches:
            return {
                "category": "Unknown",
                "confidence": 0.0,
                "source": self.name,
                "matches": [],
            }

        best = matches[0]
        confidence = min(0.99, max(best["score"], 0.0))
        category = best["category"] if confidence >= 0.65 else "Unknown"

        return {
            "category": category,
            "confidence": confidence,
            "source": self.name,
            "matches": matches,
        }
