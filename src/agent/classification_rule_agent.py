from typing import Dict, Any
from src.agent.base import Agent


RULES = {
    "Subscriptions": ["spotify", "netflix", "prime", "icloud"],
    "Transport": ["uber", "bolt", "tram", "metro", "bus", "taxi"],
    "Food": ["restaurant", "ristorante", "bar", "cafe", "pizzeria"],
    "Shopping": ["amazon", "zalando", "ikea"],
    "Utilities": ["enel", "eni", "energia", "gas"],
}


class RuleClassificationAgent(Agent):
    name = "rule_classifier"

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        description = input.get("description", "").lower()

        for category, keywords in RULES.items():
            for kw in keywords:
                if kw in description:
                    return {
                        "category": category,
                        "confidence": 0.9,
                        "source": "rule",
                    }

        return {
            "category": "Other",
            "confidence": 0.1,
            "source": "rule",
        }