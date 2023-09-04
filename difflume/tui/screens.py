# mypy: disable-error-code="override, misc"
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Generator, Literal

from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, Markdown, Static

from difflume.tui import modals
from difflume.tui.widgets import DiffWidget, ModuleWidget, PanelView

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from difflume.diffapp.modules import Module


class ErrorScreen(Screen):
    BINDINGS = [Binding("escape,space,q", "pop_screen", "Close", show=True)]

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield Static("Error")
        yield Footer()


class HelpScreen(Screen):
    MD_PATH = Path(__file__).parent / "help.md"
    BINDINGS = [
        Binding("escape,space,q,question_mark", "pop_screen", "Close", show=True)
    ]

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield Markdown(self.MD_PATH.read_text())
        yield Footer()


class DiffScreen(Screen):
    CSS_PATH = os.path.join("css", "main.tcss")
    BINDINGS = [
        Binding("question_mark", "push_screen('help')", "Help", key_display="?"),
        Binding("f", "toggle_full_screen", "Full Screen", show=True),
        Binding(
            "c",
            "toggle_class('PanelContent', 'centered-top')",
            "Center text",
            show=True,
        ),
        Binding("f1", "select_file('left')", "Select Left File", show=True),
        Binding("f3", "select_file('right')", "Select Right File", show=True),
    ]

    async def action_toggle_full_screen(self) -> None:
        await self.app.action_toggle_class("PanelView", "disabled")
        await self.app.action_remove_class("PanelView:focus", "disabled")
        await self.app.action_toggle_class("PanelView:focus", "fullscreen")

    async def action_select_file(self, panel: Literal["left", "right"]) -> None:
        def select_module_callback(module: Module) -> None:
            self.run_worker(self.load_panels(module, panel=panel), exclusive=True)

        def callback(modal_type: str) -> None:
            klass = getattr(modals, modal_type)
            self.app.push_screen(klass(), select_module_callback)

        await self.app.push_screen(modals.OpenFileModal(), callback)

    async def load_panels(
        self, module: Module, *, panel: Literal["left", "right"]
    ) -> None:
        module_widget = self.query_one(f"#{panel}-text", ModuleWidget)
        diff_widget_update = getattr(
            self.query_one("#diff-text", DiffWidget), f"update_{panel}"
        )

        # resetting content
        module_widget.update(module)
        diff_widget_update(module)

        await module.load()
        module_widget.update(module)
        diff_widget_update(module)

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield Header()
        with Horizontal():
            with PanelView():
                yield ModuleWidget(None, id="left-text")
            with PanelView():
                yield DiffWidget(None, None, id="diff-text")
            with PanelView():
                yield ModuleWidget(None, id="right-text")
        yield Footer()
