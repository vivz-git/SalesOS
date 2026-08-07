from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class ResearchProviderInterface(ABC):
    """Abstract interface for external research and intelligence providers.

    Allows plugging in future LLMs, Web Search APIs (Tavily/Exa/Firecrawl), or custom crawlers
    without mutating core FastAPI application or workspace business logic.
    """

    @abstractmethod
    def execute_research_job(
        self,
        workspace_id: UUID,
        brief_id: UUID,
        account_id: UUID,
        contact_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Execute or trigger an asynchronous research job."""
        pass
