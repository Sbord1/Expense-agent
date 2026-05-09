from typing import Dict, Any
from src.agent.base import Agent


class ClassificationVerificationAgent(Agent):
    name = "verification_agent"

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        candidate = input.get("candidate", {})
        retrieval = input.get("retrieval", {})
        rule = input.get("rule", {})

        category = candidate.get("category", "Unknown")
        confidence = candidate.get("confidence", 0.0)
        notes = []

        if category == "Unknown":
            return {
                "category": category,
                "confidence": confidence,
                "source": self.name,
                "notes": ["no_candidate"],
            }

        if retrieval.get("category") != "Unknown" and retrieval.get("category") != category:
            notes.append("retrieval_disagreement")
            confidence = min(confidence, retrieval.get("confidence", 0.5))

        if rule.get("category") != "Other" and rule.get("category") != category:
            notes.append("rule_disagreement")
            confidence = min(confidence, rule.get("confidence", 0.5))

        if candidate.get("source") == "llm" and notes:
            confidence = min(confidence, 0.65)
            notes.append("llm_verified")

        if not notes:
            notes.append("consensus")

        return {
            "category": category,
            "confidence": confidence,
            "source": self.name,
            "notes": notes,
        }
