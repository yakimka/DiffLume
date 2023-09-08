# mypy: disable-error-code="override, misc"
from __future__ import annotations

import contextlib
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
from textual.widgets import Footer, Header, Markdown

from difflume.diffapp.differ import DiffType, HighlightType, create_diff
from difflume.diffapp.modules import Module, ReadError, TextType
from difflume.tui import modals
from difflume.tui.widgets import LeftPanel, MiddlePanel, Panel, PanelType, RightPanel

if TYPE_CHECKING:
    from textual.app import ComposeResult


class HelpScreen(Screen):
    MD_PATH = Path(__file__).parent / "help.md"
    BINDINGS = [
        Binding("escape,space,q,й,question_mark", "pop_screen", "Close", show=True)
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
        Binding(
            "question_mark,comma,&,.,/", "push_screen('help')", "Help", key_display="?"
        ),
        Binding("f1", "select_file('left')", "Open Left", show=True),
        Binding("f2", "select_file('right')", "Open Right", show=True),
        Binding("[,х", "prev_revision", "Prev Revision", show=False),
        Binding("],ъ,ї", "next_revision", "Next Revision", show=False),
        Binding("{,Х", "prev_revision_sync", "Prev Revision Sync", show=False),
        Binding("},Ъ,Ї", "next_revision_sync", "Next Revision Sync", show=False),
        Binding("f,а", "toggle_full_screen", "Full Screen", show=True),
        Binding(
            "c,с",
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

    def action_prev_revision(self) -> None:
        self.prev_revision(self.query_panel(PanelType.FOCUS))

    def action_next_revision(self) -> None:
        self.next_revision(self.query_panel(PanelType.FOCUS))

    def action_prev_revision_sync(self) -> None:
        self.prev_revision(
            *[
                self.query_panel(panel_type)
                for panel_type in (PanelType.LEFT, PanelType.RIGHT)
            ]
        )

    def action_next_revision_sync(self) -> None:
        self.next_revision(
            *[
                self.query_panel(panel_type)
                for panel_type in (PanelType.LEFT, PanelType.RIGHT)
            ]
        )

    def prev_revision(self, *panel: Panel) -> None:
        try:
            indexes = [p.revisions.index(p.current_revision or "") for p in panel]
        except ValueError:
            return
        if any(i == len(p.revisions) - 1 for i, p in zip(indexes, panel)):
            return
        for i, p in zip(indexes, panel):
            self.set_revision(p.revisions[i + 1], panel=p)
            if i + 2 < len(p.revisions):
                self.preload_revision(p.revisions[i + 2], panel=p)

    def next_revision(self, *panel: Panel) -> None:
        try:
            indexes = [p.revisions.index(p.current_revision or "") for p in panel]
        except ValueError:
            return
        if 0 in indexes:
            return
        for i, p in zip(indexes, panel):
            self.set_revision(p.revisions[i - 1], panel=p)
            if i - 2 >= 0:
                self.preload_revision(p.revisions[i - 2], panel=p)

    @work
    async def load_panel(self, module: Module, *, panel_type: PanelType) -> None:
        self.set_loading_styles(panel_type)
        self.modules[panel_type] = module

        try:
            await module.load()
        except ReadError as e:
            self.show_error(str(e))
            self.set_empty_styles(panel_type)
            return

        panel = self.query_panel(panel_type)
        panel.revisions = list(module.revisions)
        panel.current_revision = next(iter(module.revisions), None)

        self.apply_module_to_panel(module, panel)
        self.update_diff_panel()

        if len(panel.revisions) > 1:
            self.preload_revision(panel.revisions[1], panel=panel)

    def show_error(self, message: str) -> None:
        self.notify(message, title="ERROR", severity="error", timeout=10)

    def set_loading_styles(self, panel_type: PanelType) -> None:
        panel = self.query_panel(panel_type)
        panel.set_loading()
        middle_panel = self.query_panel(PanelType.MIDDLE)
        middle_panel.update()

    def set_empty_styles(self, panel_type: PanelType) -> None:
        panel = self.query_panel(panel_type)
        panel.set_empty()
        middle_panel = self.query_panel(PanelType.MIDDLE)
        middle_panel.update()

    def apply_module_to_panel(self, module: Module | None, panel: Panel) -> None:
        if module is None:
            panel.set_empty()
            return
        highlighter = get_highlighter(
            module.get_content(panel.current_revision).text_type
        )
        panel.update(highlighter(Text(module.get_content(panel.current_revision).text)))
        panel.revisions = list(module.revisions)

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
            DiffType(middle_panel.current_diff_type),
        )
        diff_highlighted = Text(diff_result.text)
        for highlight_type, regexp in diff_result.highlight_regexps:
            diff_highlighted.highlight_regex(
                regexp, Style(bgcolor=DIFF_COLORS[highlight_type])
            )
        middle_panel.update(diff_highlighted)

    def on_panel_revision_selected(self, event: Panel.RevisionSelected) -> None:
        panel = self.query_panel(event.panel_type)
        self.set_revision(event.revision, panel=panel)

    @work
    async def set_revision(self, revision: str, *, panel: Panel) -> None:
        self.set_loading_styles(panel.TYPE)
        module = self.modules[panel.TYPE]
        assert module, "Unexpected empty module"

        try:
            await module.load_revision(revision)
        except ReadError as e:
            self.show_error(str(e))
            self.set_empty_styles(panel.TYPE)
            return

        panel.current_revision = revision

        self.apply_module_to_panel(module, panel)
        self.update_diff_panel()

    @work
    async def preload_revision(self, revision: str, *, panel: Panel) -> None:
        module = self.modules[panel.TYPE]
        assert module, "Unexpected empty module"

        # if we can't load revision, just ignore it
        # it is not critical for user
        with contextlib.suppress(ReadError):
            await module.load_revision(revision)

    async def on_panel_sync_panels_request(
        self, event: Panel.SyncPanelsRequest
    ) -> None:
        panel = self.query_panel(event.panel_type)
        self.sync_panels(panel)

    def sync_panels(self, from_panel: Panel) -> None:
        module = self.modules[from_panel.TYPE]
        self.modules[PanelType.LEFT] = self.modules[PanelType.RIGHT] = module
        to_panel = self.query_panel(
            next(
                type_
                for type_ in (PanelType.LEFT, PanelType.RIGHT)
                if type_ != from_panel.TYPE
            )
        )
        to_panel.revisions = from_panel.revisions
        to_panel.current_revision = from_panel.current_revision
        self.apply_module_to_panel(module, to_panel)
        self.update_diff_panel()

    def on_panel_diff_type_selected(
        self,
        event: Panel.DIffTypeSelected,  # noqa: U100
    ) -> None:
        self.update_diff_panel()

    def on_mount(self) -> None:
        self.query_panel(PanelType.LEFT).set_empty()
        self.query_panel(PanelType.MIDDLE).update("")
        self.query_panel(PanelType.RIGHT).set_empty()
