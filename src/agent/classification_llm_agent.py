from typing import Dict, Any
from src.agent.base import Agent
import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class LLMClassificationAgent(Agent):
    name = "llm_classifier"

    def __init__(self):
        if OpenAI is None or not os.getenv("OPENAI_API_KEY"):
            self.client = None
        else:
            self.client = OpenAI()

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        if self.client is None:
            raise RuntimeError("LLM not available")

        description = input["description"]
        amount = input["amount"]

        prompt = f"""
        Categorize this transaction.

        Description: "{description}"
        Amount: {amount}

        Categories:
        Food, Transport, Rent, Subscriptions, Utilities, Shopping, Leisure, Other

        Return JSON:
        {{
          "category": "...",
          "confidence": 0.0-1.0
        }}
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        result = eval(response.choices[0].message.content)

        return {
            "category": result["category"],
            "confidence": result["confidence"],
            "source": "llm",
        }