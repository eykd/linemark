"""Claude agent adapter: Concrete implementation of the AgentPort interface."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from linemark.domain.agents import AgentStreamEvent, StreamEventType
from linemark.ports.agents import AgentPort

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)


class StubAgent(AgentPort):
    """A stub agent adapter for testing."""

    async def submit_query(self, query: str) -> None:  # noqa: ARG002
        """Query the agent."""
        return

    async def receive_events(self) -> AsyncGenerator[AgentStreamEvent, None]:  # type: ignore[override]
        """Receive messages from the stub agent."""
        yield AgentStreamEvent(
            content='',
            role='assistant',
            block_type='text',
            event_type=StreamEventType.START_CONTENT_BLOCK,
        )
        yield AgentStreamEvent(
            content='Hello, world!',
            role='assistant',
            block_type='text',
            event_type=StreamEventType.DELTA_CONTENT_BLOCK,
        )
        yield AgentStreamEvent(
            content='',
            role='assistant',
            block_type='text',
            event_type=StreamEventType.END_CONTENT_BLOCK,
        )
        yield AgentStreamEvent(
            content='Total Cost: $0.0000',
            role='result',
            block_type='result',
            event_type=StreamEventType.RESULT,
        )
