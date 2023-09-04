from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Generator, Literal

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, Markdown

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


class HelpScreen(Screen):
    MD_PATH = Path(__file__).parent / "help.md"
    BINDINGS = [Binding("escape,space,q,question_mark", "pop_screen", "Close", show=True)]

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield Markdown(self.MD_PATH.read_text())
        yield Footer()


class DiffScreen(Screen):
    app: DiffLume
    CSS_PATH = "css/main.tcss"
    BINDINGS = [
        Binding("question_mark", "push_screen('help')", "Help", key_display="?"),
        Binding("f", "toggle_full_screen", "Full Screen", show=True),
        Binding("c", "toggle_class('PanelContent', 'centered-top')", "Center text", show=True),
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
        def callback(module: FSModule) -> None:
            self.run_worker(self.load_panels(module, panel=panel), exclusive=True)
        await self.app.push_screen(SelectFileModal(), callback)

    async def load_panels(self, module, *, panel: Literal["left", "right"]) -> None:
        setattr(self.app, f"{panel}_module", module)
        module_widget = self.query_one(f"#{panel}-text", ModuleWidget)
        diff_widget = self.query_one("#diff-text", DiffWidget)
        # resetting content
        module_widget.update(module)
        diff_widget.update(self.left_module, self.right_module)
        await module.read()
        module_widget.update(module)
        diff_widget.update(self.left_module, self.right_module)

    async def on_mount(self) -> None:
        self.run_worker(self.load_panels(self.left_module, panel="left"))
        self.run_worker(self.load_panels(self.right_module, panel="right"))

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield Header()
        with Horizontal():
            with PanelView():
                yield ModuleWidget(self.left_module, id="left-text")
            with PanelView():
                yield DiffWidget(self.left_module, self.right_module, id="diff-text")
            with PanelView():
                yield ModuleWidget(self.right_module, id="right-text")
        yield Footer()
