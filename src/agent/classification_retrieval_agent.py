from typing import Dict, Any
from src.agent.base import Agent
from src.agent.embedding_similarity_agent import EmbeddingSimilarityAgent


class ClassificationRetrievalAgent(Agent):
    name = "retrieval_classifier"

    def __init__(self):
        self.memory_agent = EmbeddingSimilarityAgent()

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        description = input.get("description", "").lower().strip()
        if not description:
            return {
                "category": "Unknown",
                "confidence": 0.0,
                "source": self.name,
                "matches": [],
            }

        result = self.memory_agent.run({"description": description})
        if result["category"] != "Unknown":
            result["source"] = self.name
            result["confidence"] = max(0.75, result["confidence"])
        return result
