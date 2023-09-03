from __future__ import annotations

import os
from typing import Generator
from typing import TYPE_CHECKING

from rich.highlighter import ReprHighlighter, JSONHighlighter, Highlighter
from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen, ModalScreen
from textual.widget import Widget
from textual.widgets import Static, Header, Footer, DirectoryTree

from difflume.diffapp.differ import create_diff, DiffType, HighlightType
from difflume.diffapp.modules import TextType, FSModule
from difflume.tui.widgets import TextViewWidget

if TYPE_CHECKING:
    from difflume.tui.app import DiffLume



class ErrorScreen(Screen):
    BINDINGS = [Binding("escape,space,q", "pop_screen", "Close", show=True)]

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield Static("Error")
        yield Footer()


class Modal(ModalScreen):
    BINDINGS = [Binding("escape,q", "pop_screen", "Close", show=True)]


class SelectFileModal(Modal):
    BINDINGS = [
        Binding("escape,q", "pop_screen", "Close", show=True),
        Binding("e", "select_file_and_close", "Select", show=True),
    ]

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield DirectoryTree(os.getcwd(), id="select-file-modal")
        yield Footer()

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.dismiss(event.path)


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
    app: DiffLume
    CSS_PATH = "css/main.tcss"
    BINDINGS = [
        Binding("f", "toggle_full_screen", "Full Screen", show=True),
        Binding("c", "toggle_class('Static', 'centered')", "Center text", show=True),
    ]

    @property
    def left_module(self) -> FSModule:
        return self.app.left_module

    @property
    def right_module(self) -> FSModule:
        return self.app.right_module

    async def action_toggle_full_screen(self) -> None:
        await self.app.action_toggle_class("VerticalScroll", "disabled")
        await self.app.action_remove_class("VerticalScroll:focus", "disabled")
        await self.app.action_toggle_class("VerticalScroll:focus", "fullscreen")

    def get_widgets(self) -> tuple[Widget, Widget, Widget]:
        left_highlighter = get_highlighter(self.left_module.content.text_type)
        left_text = self.left_module.content.text
        left_widget = Static(left_highlighter(Text(left_text)))
        right_highlighter = get_highlighter(self.right_module.content.text_type)
        right_text = self.right_module.content.text
        right_widget = Static(right_highlighter(Text(right_text)))

        diff_result = create_diff(left_text, right_text, DiffType.NDIFF)
        diff_highlighted = Text(diff_result.text)
        for highlight_type, regexp in diff_result.highlight_regexp.items():
            diff_highlighted.highlight_regex(regexp, Style(bgcolor=DIFF_COLORS[highlight_type]))
        return left_widget, Static(diff_highlighted), right_widget

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield Header()
        left, middle, right = self.get_widgets()
        with Horizontal():
            with VerticalScroll():
                yield left
            with VerticalScroll():
                yield middle
            with VerticalScroll():
                yield right
        yield Footer()
