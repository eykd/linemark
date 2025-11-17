from collections.abc import Callable

from textual.pilot import Pilot

from linemark.adapters.agents.stubs import StubAgent
from linemark.cli.tui import AgentApp


def test_agent_app_basic_integration(snap_compare: Callable) -> None:  # type: ignore[type-arg]
    async def run_before(pilot: Pilot[AgentApp]) -> None:
        await pilot.press('h', 'e', 'l', 'l', 'o', '\n', 'w', 'o', 'r', 'l', 'd', '\n')
        await pilot.press('enter')
        await pilot.press('h', 'o', 'w', ' ', 'a', 'r', 'e', ' ', 'y', 'o', 'u', '?')

    assert snap_compare(AgentApp(agent=StubAgent(), testing=True), run_before=run_before)
