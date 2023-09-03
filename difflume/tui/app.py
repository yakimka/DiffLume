from textual.app import App
from textual.binding import Binding

from difflume.tui.screens import DiffScreen, ErrorScreen


class DiffLume(App[None]):
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True, priority=True),
    ]

    SCREENS = {
        "error_screen": ErrorScreen,
    }

    def __init__(self, *args, left_module, right_module, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.left_module = left_module
        self.right_module = right_module

    async def on_mount(self) -> None:
        await self.push_screen(DiffScreen())
