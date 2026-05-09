import json
import os
from typing import Dict, Any
from src.agent.base import Agent

RULES_FILE = "data/rules.json"


def load_rules() -> Dict[str, list]:
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


RULES = load_rules()


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