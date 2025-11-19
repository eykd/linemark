"""Claude agent adapter: Concrete implementation of the AgentPort interface."""

from __future__ import annotations  # pragma: no cover

import logging  # pragma: no cover
import textwrap  # pragma: no cover
from typing import TYPE_CHECKING, ClassVar, Self  # pragma: no cover

from claude_agent_sdk import (  # pragma: no cover
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)
from claude_agent_sdk.types import (
    AgentDefinition,
    McpServerConfig,
    PermissionMode,
    StreamEvent,
    SystemPromptPreset,
)  # pragma: no cover

from linemark.domain.agents import AgentStreamEvent, StreamEventType  # pragma: no cover
from linemark.ports.agents import AgentPort  # pragma: no cover

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncGenerator
    from pathlib import Path
    from types import TracebackType

logger = logging.getLogger(__name__)  # pragma: no cover


class ClaudeAgent(AgentPort):  # pragma: no cover
    """An agent adapter backed by the Claude SDK"""

    system_prompt: ClassVar[str | SystemPromptPreset | None] = None
    model: ClassVar[str] = 'sonnet'
    allowed_tools: ClassVar[list[str]] = []
    agents: ClassVar[dict[str, AgentDefinition] | None] = None
    mcp_servers: ClassVar[dict[str, McpServerConfig] | str | Path] = {}
    permission_mode: ClassVar[PermissionMode] = 'default'

    client: ClaudeSDKClient

    def __init__(self) -> None:
        super().__init__()
        # Build the system prompt append, handling both str and SystemPromptPreset types
        append_text = ''
        if self.system_prompt and isinstance(self.system_prompt, str):
            append_text = textwrap.dedent(self.system_prompt.rstrip())

        self.client = ClaudeSDKClient(
            options=ClaudeAgentOptions(
                model=self.model,
                system_prompt={
                    'type': 'preset',
                    'preset': 'claude_code',
                    'append': append_text,
                },
                allowed_tools=self.allowed_tools,
                agents=self._process_agents(),
                mcp_servers=self.mcp_servers,
                permission_mode=self.permission_mode,
                # Receive partial messages for streaming results
                include_partial_messages=True,
            )
        )

    def _process_agents(self) -> dict[str, AgentDefinition] | None:
        """Process the agents."""
        return (
            {
                name: AgentDefinition(
                    description=agent_def.description,
                    prompt=textwrap.dedent(agent_def.prompt.rstrip()) if agent_def.prompt else '',
                    tools=agent_def.tools,
                    model=agent_def.model,
                )
                for name, agent_def in self.agents.items()
            }
            if self.agents
            else None
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
