from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Literal

from rich.highlighter import Highlighter, JSONHighlighter, ReprHighlighter
from rich.style import Style
from rich.text import Text
from textual import work
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.message import Message
from textual.widget import Widget

from difflume.diffapp.differ import DiffType, HighlightType, create_diff
from difflume.diffapp.modules import Module, TextType, Content
from difflume.tui import modals

if TYPE_CHECKING:
    from rich.console import RenderableType


class PanelView(VerticalScroll):
    BINDINGS = [
        Binding("r", "select_revision", "Revisions", show=True),
    ]

    async def action_select_revision(self) -> None:
        try:
            module_widget = self.query_one(ModuleWidget)
        except NoMatches:
            return

        module = module_widget.module
        if not module or not module.ready() or not module.revisions:
            return

        def set_revision(revision: str) -> None:
            self._set_revision(module_widget, revision)

        await self.app.push_screen(modals.SelectRevisionModal(module_widget.current_revision, module.revisions), set_revision)

    @work
    async def _set_revision(self, module_widget: ModuleWidget, revision: str) -> None:
        await module_widget.module.load_revision(revision)
        module_widget.set_revision(revision)


def get_highlighter(text_type: TextType) -> Highlighter:
    if text_type is TextType.JSON:
        return JSONHighlighter()
    return ReprHighlighter()


class PanelContent(Widget, inherit_bindings=False):
    DEFAULT_CSS = """
    PanelContent {
        height: auto;
    }
    """

    def _set_waiting_style(self) -> None:
        self.add_class("centered-middle")

    def _remove_waiting_style(self) -> None:
        self.remove_class("centered-middle")


class ModuleWidget(PanelContent):
    _module: Module | None

    class Updated(Message):
        pass

    def __init__(
        self,
        module: Module | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.module = module
        self.current_revision = None

    @property
    def module(self) -> Module | None:
        return self._module

    @module.setter
    def module(self, module: Module | None) -> None:
        self._module = module

    def render(self) -> RenderableType:
        if not self.module:
            self._set_waiting_style()
            return Text("Empty")
        if not self.module.ready():
            self._set_waiting_style()
            return Text("Loading...")
        left_highlighter = get_highlighter(self.content.text_type)
        left_text = self.content.text
        self._remove_waiting_style()
        return left_highlighter(Text(left_text))

    @property
    def content(self) -> Content:
        if self.current_revision is None:
            return self.module.content
        return self.module.revisions_content[self.current_revision]

    def update(self, module: Module | None) -> None:
        self.module = module
        if self.current_revision is None and module and module.revisions:
            self.current_revision = module.revisions[0]
        self.refresh(layout=True)
        self.post_message(self.Updated())

    def set_revision(self, revision: str) -> None:
        self.current_revision = revision
        self.refresh(layout=True)
        self.post_message(self.Updated())


DIFF_COLORS = {
    HighlightType.ADDED: "dark_green",
    HighlightType.REMOVED: "red",
    HighlightType.EXPLANATION: "bright_black",
}


class DiffWidget(PanelContent):
    _left_module: Module | None
    _right_module: Module | None

    def __init__(
        self,
        left_module: Module | None = None,
        right_module: Module | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.left_module = left_module
        self.right_module = right_module

    @property
    def left_module(self) -> Module | None:
        return self._left_module

    @left_module.setter
    def left_module(self, left_module: Module | None) -> None:
        self._left_module = left_module

    @property
    def right_module(self) -> Module | None:
        return self._right_module

    @right_module.setter
    def right_module(self, right_module: Module | None) -> None:
        self._right_module = right_module

    def render(self) -> RenderableType:
        if not self.left_module or not self.right_module:
            self._set_waiting_style()
            return Text("")
        if not self.left_module.ready() or not self.right_module.ready():
            self._set_waiting_style()
            return Text("Loading...")

        diff_result = create_diff(
            self.left_module.content.text,
            self.right_module.content.text,
            DiffType.NDIFF,
        )
        diff_highlighted = Text(diff_result.text)
        for highlight_type, regexp in diff_result.highlight_regexp.items():
            diff_highlighted.highlight_regex(
                regexp, Style(bgcolor=DIFF_COLORS[highlight_type])
            )
        self._remove_waiting_style()
        return diff_highlighted

    def update(self, left_module: Module | None, right_module: Module | None) -> None:
        self.left_module = left_module
        self.right_module = right_module
        self.refresh(layout=True)

    def update_left(self, left_module: Module | None) -> None:
        self.left_module = left_module
        self.refresh(layout=True)

    def update_right(self, right_module: Module | None) -> None:
        self.right_module = right_module
        self.refresh(layout=True)
