"""Agent port contract"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

from linemark.domain.messages import Switchboard

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from types import TracebackType

    from linemark.domain.agents import AgentStreamEvent


class AgentPort(ABC):
    """Agent port contract."""

    switchboard: Switchboard = Switchboard()

    @abstractmethod
    async def submit_query(self, query: str) -> None:
        """Submit a query to the agent."""

    @abstractmethod
    async def receive_events(self) -> AsyncGenerator[AgentStreamEvent, None]:
        """Receive stream events from the agent."""

    async def __aenter__(self) -> Self:
        """Enter the context manager."""
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        """Exit the context manager."""
        return
