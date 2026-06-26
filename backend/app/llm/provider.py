from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        pass
