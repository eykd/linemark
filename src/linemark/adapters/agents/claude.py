"""Claude agent adapter: Concrete implementation of the AgentPort interface."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)
from claude_agent_sdk.types import StreamEvent

from linemark.domain.agents import AgentStreamEvent, StreamEventType
from linemark.ports.agents import AgentPort

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncGenerator
    from types import TracebackType

logger = logging.getLogger(__name__)


class ClaudeAgent(AgentPort):  # pragma: no cover
    """An agent adapter backed by the Claude SDK"""

    system_prompt: str = ''
    model: str = 'sonnet'

    def __init__(self) -> None:
        self.client = ClaudeSDKClient(
            options=ClaudeAgentOptions(
                model=self.model,
                system_prompt=self.system_prompt,
                # Receive partial messages for streaming results
                include_partial_messages=True,
            )
        )

    async def __aenter__(self) -> Self:
        await self.client.connect()
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        await self.client.disconnect()

    async def submit_query(self, query: str) -> None:
        """Query the agent."""
        await self.client.query(query)

    async def receive_events(self) -> AsyncGenerator[AgentStreamEvent, None]:  # type: ignore[override]
        """Receive messages from the Claude SDK."""
        current_block_type: str | None = None
        async for message in self.client.receive_messages():
            match message:
                case StreamEvent():
                    match message.event['type']:
                        case 'content_block_start':
                            current_block_type = message.event['content_block']['type']
                            yield AgentStreamEvent(
                                content='',
                                role='assistant',
                                block_type=current_block_type,
                                event_type=StreamEventType.START_CONTENT_BLOCK,
                            )
                        case 'content_block_stop':
                            yield AgentStreamEvent(
                                content='',
                                role='assistant',
                                block_type=current_block_type,
                                event_type=StreamEventType.END_CONTENT_BLOCK,
                            )
                        case 'content_block_delta':
                            match message.event['delta']['type']:
                                case 'text_delta':
                                    yield AgentStreamEvent(
                                        content=message.event['delta']['text'],
                                        role='assistant',
                                        block_type=current_block_type,
                                        event_type=StreamEventType.DELTA_CONTENT_BLOCK,
                                    )
                        case _:
                            logger.info(f'Unknown stream event type: {message.event["type"]}:\n{message!r}')  # noqa: G004
                case ResultMessage():  # This is the last message in the response.
                    yield AgentStreamEvent(
                        content=f'Total Cost: ${message.total_cost_usd:.4f}',
                        role='result',
                        block_type='result',
                        event_type=StreamEventType.RESULT,
                    )
                case _:
                    pass
