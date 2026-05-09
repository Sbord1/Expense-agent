from src.agent.classification_rule_agent import RuleClassificationAgent
from src.agent.classification_llm_agent import LLMClassificationAgent
from src.agent.classification_retrieval_agent import ClassificationRetrievalAgent
from src.agent.classification_verification_agent import ClassificationVerificationAgent
from src.agent.feedback_agent import lookup_feedback


class ClassificationOrchestrator:
    def __init__(self):
        self.rule_agent = RuleClassificationAgent()
        self.llm_agent = LLMClassificationAgent()
        self.retrieval_agent = ClassificationRetrievalAgent()
        self.verifier = ClassificationVerificationAgent()

    def classify(self, description: str, amount: float, transaction_id: str = None):
        description = description.lower().strip()

        # 1️⃣ known user feedback takes precedence
        feedback_category = lookup_feedback(description)
        if feedback_category:
            return {
                "category": feedback_category,
                "confidence": 1.0,
                "source": "feedback",
                "debug": {
                    "reason": "user_feedback",
                },
            }

        # 2️⃣ retrieval-first: use semantic memory for similar historical transactions
        retrieval = self.retrieval_agent.run({"description": description})
        if retrieval["confidence"] >= 0.75 and retrieval["category"] != "Unknown":
            final = retrieval
        else:
            # 3️⃣ rule-based fallback for predictable patterns
            rule = self.rule_agent.run({"description": description})
            if rule["confidence"] >= 0.85:
                final = rule
            else:
                # 4️⃣ selective LLM reasoning only when needed
                try:
                    llm_result = self.llm_agent.run({"description": description, "amount": amount})
                except Exception:
                    llm_result = rule
                final = llm_result if llm_result.get("confidence", 0.0) >= 0.5 else rule

        # 5️⃣ verify and explain the final decision
        verification = self.verifier.run({
            "candidate": final,
            "retrieval": retrieval,
            "rule": rule if "rule" in locals() else {"category": "Other", "confidence": 0.1},
        })

        if transaction_id and verification["category"] not in {"Other", "Unknown"}:
            self.retrieval_agent.memory_agent.upsert_memory(
                transaction_id,
                description,
                verification["category"],
            )

        return {
            "category": verification["category"],
            "confidence": verification["confidence"],
            "source": verification["source"],
            "debug": {
                "retrieval": retrieval,
                "rule": rule if "rule" in locals() else None,
                "verified": verification,
            },
        }