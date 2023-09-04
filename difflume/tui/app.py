from dataclasses import dataclass

from httpx import AsyncClient
from textual.app import App
from textual.binding import Binding

from difflume.tui.screens import DiffScreen, ErrorScreen, HelpScreen


@dataclass
class Deps:
    http_client: AsyncClient

    @classmethod
    def create(cls) -> "Deps":
        return cls(
            http_client=AsyncClient(follow_redirects=True, verify=False)  # noqa: S501
        )

    async def close(self) -> None:
        await self.http_client.aclose()


class DiffLume(App[None]):
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True, priority=True),
    ]

    SCREENS = {
        "error_screen": ErrorScreen,
        "help": HelpScreen,
    }

    deps: Deps

    async def on_mount(self) -> None:
        self.deps = Deps.create()
        await self.push_screen(DiffScreen())

    async def on_unmount(self) -> None:
        await self.deps.close()
