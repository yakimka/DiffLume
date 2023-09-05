# mypy: disable-error-code="override, misc"
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Generator, Literal

from rich.highlighter import Highlighter, JSONHighlighter, ReprHighlighter
from rich.style import Style
from rich.text import Text
from textual import work
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, Markdown, Static

from difflume.diffapp.differ import DiffType, HighlightType, create_diff
from difflume.diffapp.modules import Module, TextType
from difflume.tui import modals
from difflume.tui.widgets import LeftPanel, MiddlePanel, Panel, PanelType, RightPanel

if TYPE_CHECKING:
    from textual.app import ComposeResult


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


def get_highlighter(text_type: TextType) -> Highlighter:
    if text_type is TextType.JSON:
        return JSONHighlighter()
    return ReprHighlighter()


DIFF_COLORS = {
    HighlightType.ADDED: "dark_green",
    HighlightType.REMOVED: "red",
    HighlightType.EXPLANATION: "bright_black",
}


class DiffScreen(Screen):
    CSS_PATH = os.path.join("css", "main.tcss")
    BINDINGS = [
        Binding("question_mark", "push_screen('help')", "Help", key_display="?"),
        Binding("f1", "select_file('left')", "Open Left", show=True),
        Binding("f2", "select_file('right')", "Open Right", show=True),
        Binding("f", "toggle_full_screen", "Full Screen", show=True),
        Binding(
            "c",
            "toggle_class('Panel Content', 'centered-top')",
            "Center text",
            show=True,
        ),
    ]

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.modules: dict[PanelType, Module | None] = {
            PanelType.LEFT: None,
            PanelType.RIGHT: None,
        }

    @property
    def left_module(self) -> Module | None:
        return self.modules[PanelType.LEFT]

    @property
    def right_module(self) -> Module | None:
        return self.modules[PanelType.RIGHT]

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield Header()
        with Horizontal():
            yield LeftPanel()
            yield MiddlePanel()
            yield RightPanel()
        yield Footer()

    def query_panel(self, panel_type: PanelType = PanelType.FOCUS) -> Panel:
        if panel_type is PanelType.FOCUS:
            return self.query_one("Panel:focus", Panel)
        return self.query_one(f"{panel_type.value.capitalize()}Panel", Panel)

    async def action_toggle_full_screen(self) -> None:
        await self.app.action_toggle_class("Panel", "disabled")
        await self.app.action_remove_class("Panel:focus", "disabled")
        await self.app.action_toggle_class("Panel:focus", "fullscreen")

    async def action_select_file(self, panel_type: Literal["left", "right"]) -> None:
        def select_module_callback(module: Module) -> None:
            self.load_panel(module, panel_type=PanelType(panel_type))

        def callback(modal_type: str) -> None:
            klass = getattr(modals, modal_type)
            self.app.push_screen(klass(), select_module_callback)

        await self.app.push_screen(modals.OpenFileModal(), callback)

    @work
    async def load_panel(self, module: Module, *, panel_type: PanelType) -> None:
        self.set_loading_styles(panel_type)
        self.modules[panel_type] = module
        await module.load()

        panel = self.query_panel(panel_type)
        panel.revisions = list(module.revisions)
        panel.current_revision = next(iter(module.revisions), None)

        self.apply_module_to_panel(module, panel)
        self.update_diff_panel()

    def set_loading_styles(self, panel_type: PanelType) -> None:
        panel = self.query_panel(panel_type)
        panel.set_loading()
        middle_panel = self.query_panel(PanelType.MIDDLE)
        middle_panel.update()

    def apply_module_to_panel(self, module: Module, panel: Panel) -> None:
        highlighter = get_highlighter(module.get_content().text_type)
        panel.update(highlighter(Text(module.get_content().text)))

    def update_diff_panel(self) -> None:
        if not self.left_module or not self.right_module:
            return
        if not self.left_module.ready() or not self.right_module.ready():
            return

        left_panel = self.query_panel(PanelType.LEFT)
        middle_panel = self.query_panel(PanelType.MIDDLE)
        right_panel = self.query_panel(PanelType.RIGHT)
        diff_result = create_diff(
            self.left_module.get_content(left_panel.current_revision).text,
            self.right_module.get_content(right_panel.current_revision).text,
            DiffType.NDIFF,
        )
        diff_highlighted = Text(diff_result.text)
        for highlight_type, regexp in diff_result.highlight_regexp.items():
            diff_highlighted.highlight_regex(
                regexp, Style(bgcolor=DIFF_COLORS[highlight_type])
            )
        middle_panel.update(diff_highlighted)

    @work
    async def on_panel_revision_selected(self, event: Panel.RevisionSelected) -> None:
        self.set_loading_styles(event.panel_type)
        module = self.modules[event.panel_type]
        assert module, "Unexpected empty module"
        await module.load_revision(event.revision)

        panel = self.query_panel(event.panel_type)
        self.apply_module_to_panel(module, panel)
        self.update_diff_panel()

    def on_mount(self) -> None:
        self.query_panel(PanelType.LEFT).set_empty()
        self.query_panel(PanelType.MIDDLE).update("")
        self.query_panel(PanelType.RIGHT).set_empty()
