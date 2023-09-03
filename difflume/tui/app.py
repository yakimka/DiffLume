from textual.app import App
from textual.binding import Binding

from difflume.diffapp.modules import FSModule
from difflume.tui.screens import ErrorScreen, DiffScreen, SelectFileModal


class DiffLume(App[None]):
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True, priority=True),

        Binding("d", "select_file", "Select File"),
    ]

    SCREENS = {
        "error_screen": ErrorScreen,
        "select_file": SelectFileModal,
    }

    def __init__(self, *args, left_module, right_module, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.left_module = left_module
        self.right_module = right_module

    async def action_select_file(self) -> None:
        async def select_file(path: str) -> None:
            module = FSModule(path)
            await module.read()
            self.left_module = module

        await self.push_screen(SelectFileModal(), select_file)

    async def on_mount(self) -> None:
        await self.push_screen(DiffScreen())
