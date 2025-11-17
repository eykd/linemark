"""Domain entities and value objects for agents."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class StreamEventType(StrEnum):
    """The type of stream event."""

    START_CONTENT_BLOCK = 'start_content_block'
    DELTA_CONTENT_BLOCK = 'delta_content_block'
    END_CONTENT_BLOCK = 'end_content_block'
    RESULT = 'result'


class AgentStreamEvent(BaseModel):
    """A stream event from the agent."""

    content: str = Field(..., description='The content of the message.')
    role: str = Field(..., description='The role of the message.')
    block_type: str = Field(..., description='The type of the block.')
    event_type: StreamEventType = Field(..., description='The event type.')
