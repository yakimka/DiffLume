from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Literal

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, Header, Static

from difflume.diffapp.modules import FSModule
from difflume.tui.modals import SelectFileModal
from difflume.tui.widgets import DiffWidget, ModuleWidget, PanelView

if TYPE_CHECKING:
    from difflume.tui.app import DiffLume


class ErrorScreen(Screen):
    BINDINGS = [Binding("escape,space,q", "pop_screen", "Close", show=True)]

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield Static("Error")
        yield Footer()


class DiffScreen(Screen):
    app: DiffLume
    CSS_PATH = "css/main.tcss"
    BINDINGS = [
        Binding("f", "toggle_full_screen", "Full Screen", show=True),
        Binding("c", "toggle_class('.panel-content', 'centered')", "Center text", show=True),
        Binding("f1", "select_file('left')", "Select Left File", show=True),
        Binding("f3", "select_file('right')", "Select Right File", show=True),
    ]

    @property
    def left_module(self) -> FSModule:
        return self.app.left_module

    @property
    def right_module(self) -> FSModule:
        return self.app.right_module

    async def action_toggle_full_screen(self) -> None:
        await self.app.action_toggle_class("PanelView", "disabled")
        await self.app.action_remove_class("PanelView:focus", "disabled")
        await self.app.action_toggle_class("PanelView:focus", "fullscreen")

    async def action_select_file(self, panel: Literal["left", "right"]) -> None:
        async def select_file(path: str) -> None:
            new_module = FSModule(path)
            await new_module.read()
            setattr(self.app, f"{panel}_module", new_module)
            self.query_one(f"#{panel}-text", ModuleWidget).update(new_module)
            self.query_one("#diff-text", DiffWidget).update(
                self.left_module, self.right_module
            )

        await self.app.push_screen(SelectFileModal(), select_file)

    def get_widgets(self) -> tuple[Widget, Widget, Widget]:
        left_widget = ModuleWidget(self.left_module, id="left-text")
        diff_widget = DiffWidget(self.left_module, self.right_module, id="diff-text")
        right_widget = ModuleWidget(self.right_module, id="right-text")

        return left_widget, diff_widget, right_widget

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield Header()
        left, middle, right = self.get_widgets()
        with Horizontal():
            with PanelView():
                yield left
            with PanelView():
                yield middle
            with PanelView():
                yield right
        yield Footer()
