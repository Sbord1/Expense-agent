from src.agent.classification_rule_agent import RuleClassificationAgent
from src.agent.classification_llm_agent import LLMClassificationAgent


class ClassificationOrchestrator:
    def __init__(self):
        self.rule_agent = RuleClassificationAgent()
        self.llm_agent = LLMClassificationAgent()

    def classify(self, description: str, amount: float):
        # 1️⃣ sempre rule-based
        result = self.rule_agent.run({
            "description": description,
            "amount": amount,
        })

        # 2️⃣ fallback a LLM solo se poco confident
        if result["confidence"] < 0.5:
            try:
                result = self.llm_agent.run({
                    "description": description,
                    "amount": amount,
                })
            except Exception:
                pass  # fallback sicuro

        return result