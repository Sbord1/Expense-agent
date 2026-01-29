from abc import ABC, abstractmethod
from typing import Dict, Any


class Agent(ABC):
    """
    Base class for all agents.
    """

    name: str

    @abstractmethod
    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent logic.

        Input and output must be JSON-serializable.
        """
        pass