from abc import ABC, abstractmethod

from app.schemas.agent import AgentResult


class BaseRecruitmentAgent(ABC):
    @abstractmethod
    def parse_message(self, message: str) -> AgentResult:
        pass
