"""Simple Command Line Agent"""

import logging
from typing import ClassVar

from textual import events, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.logging import TextualHandler
from textual.widgets import (
    Footer,
    Header,
    Markdown,
    MarkdownViewer,
    Static,
    TextArea,
)

from linemark.adapters.agents.s5.assistant import S5AssistantAgent
from linemark.domain.agents import StreamEventType
from linemark.ports.agents import AgentPort

logger = logging.getLogger(__name__)


class UserInputTextArea(TextArea):
    """A TextArea for user input."""

    async def _on_key(self, event: events.Key) -> None:
        await super()._on_key(event)
        match event.character:
            case '\n':
                self.insert('\n')


class AgentApp(App[None]):
    """A Claude Agent app."""

    # Textual lays out the UI using CSS.
    CSS = """
        Screen {
            layout: grid;
            grid-size: 1 3;
            grid-columns: 1fr;
            grid-rows: 80% 1fr 20%;
        }

        #markdown {
            height: 100%;
            width: 100%;
        }
        #status {
            height: 100%;
        }
        #input {
            height: 100%;
        }
    """

    BINDINGS: ClassVar[list[Binding]] = [  # type: ignore[assignment]
        # priority=True overrides built-in widget bindings
        Binding('enter', 'submit_query', 'Submit Query', priority=True),
    ]

    s5_agent: AgentPort

    def __init__(self, agent: AgentPort = None, initial_query: str | None = None, testing: bool = False) -> None:  # noqa: FBT001, FBT002
        super().__init__()
        self.s5_agent = agent if agent is not None else S5AssistantAgent()  # pragma: no cover
        self.initial_query = initial_query or "Let's get started!"
        self.testing = testing

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield MarkdownViewer(id='markdown', show_table_of_contents=False)
        yield Static('Waiting for input…', id='status')
        yield UserInputTextArea(placeholder='Enter your query here...', id='input')
        yield Footer()

    def on_load(self) -> None:
        """Event handler for when the app is loaded and ready."""
        logging.basicConfig(level=logging.INFO, handlers=[TextualHandler()])

    async def on_mount(self) -> None:
        """Event handler for after all UI widgets are mounted."""
        # We can query by CSS selector:
        self.markdown_viewer = self.query_one('#markdown')
        # Disable keyboard focus on the Markdown viewer:
        self.markdown_viewer.can_focus = False
        # Anchor the scrollable area to the bottom of the Markdown document:
        self.markdown_viewer.anchor()

        # We can also query by widget type. The `Markdown` widget is
        # implicitly created by `MarkdownViewer`:
        self.markdown = self.query_one(Markdown)
        self.markdown.can_focus = False
        # Send all mouse scroll events to the Markdown document:
        self.markdown.capture_mouse()

        # We'll append to this stream as the agent responds:
        self.markdown_stream = Markdown.get_stream(self.markdown)

        self.input_widget: TextArea = self.query_one('#input')  # type: ignore[assignment]
        # Capture keyboard focus for the input text area:
        self.input_widget.focus()

        # Start the S5 agent worker once the UI is ready:
        self._run_s5_agent()

    async def action_submit_query(self) -> None:
        """Submit the user's query to the agent."""
        # Send the user's message to the agent:
        user_query = self.input_widget.text
        await self.s5_agent.submit_query(user_query)
        self.input_widget.text = ''
        await self.append_markdown(f'**User:** {user_query}\n\n')

    @work(exclusive=True)
    async def _run_s5_agent(self) -> None:  # noqa: C901
        """Run the System 5 agent to receive messages in the background."""
        async with self.s5_agent:
            await self.append_markdown('=== System 5 agent started ===\n\n')
            if self.initial_query:
                initial_query = f"{self.initial_query}\n\nLet's get started!"
            else:
                initial_query = "Let's get started!"
            await self.s5_agent.submit_query(initial_query)
            await self.append_markdown(f'**User:** {initial_query}\n\n')
            # Receive messages from the agent in a loop:
            while True:
                async for event in self.s5_agent.receive_events():  # type: ignore[attr-defined]
                    match event.event_type:
                        case StreamEventType.START_MESSAGE:
                            self.query_one('#status').loading = True
                        case StreamEventType.END_MESSAGE:
                            self.query_one('#status').loading = False
                        case StreamEventType.START_CONTENT_BLOCK:
                            await self.append_markdown(f'**{event.role.replace("_", " ").upper()}:** ')
                        case StreamEventType.DELTA_CONTENT_BLOCK:
                            await self.append_markdown(event.content)
                        case StreamEventType.END_CONTENT_BLOCK:
                            await self.append_markdown('\n\n')
                        case StreamEventType.RESULT:  # pragma: no branch
                            await self.append_markdown(f'=== {event.content} ===\n\n')
                if self.testing:  # Don't run the agent forever in testing mode.  # pragma: no branch
                    break

    async def append_markdown(self, text: str) -> None:
        """Append text to the Markdown document.

        This uses the more-efficient stream-based approach to appending text
        to the Markdown document.
        """
        await self.markdown_stream.write(text)
