# mypy: disable-error-code="override, misc"
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Generator

from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widgets import Static

from difflume.diffapp.differ import DiffType
from difflume.tui import modals

if TYPE_CHECKING:
    from rich.console import RenderableType
    from textual.app import ComposeResult


class PanelType(Enum):
    LEFT = "left"
    MIDDLE = "middle"
    RIGHT = "right"
    FOCUS = "focus"


class Content(Static):
    pass


class Panel(VerticalScroll):
    TYPE: PanelType

    class RevisionSelected(Message):
        def __init__(self, revision: str, *, panel_type: PanelType) -> None:
            self.revision = revision
            self.panel_type = panel_type
            super().__init__()

    class SyncPanelsRequest(Message):
        def __init__(self, panel_type: PanelType) -> None:
            super().__init__()
            self.panel_type = panel_type

    class DIffTypeSelected(Message):
        def __init__(self, diff_type: DiffType, *, panel_type: PanelType) -> None:
            super().__init__()
            self.diff_type = diff_type
            self.panel_type = panel_type

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.revisions: list[str] = []
        self.current_revision: str | None = None
        self.diff_types: list[str] = [diff.value for diff in DiffType]
        self.current_diff_type: str = DiffType.NDIFF_COLLAPSED.value

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield Content()

    def update(self, renderable: RenderableType = "") -> None:
        self.query_one(Content).update(renderable)
        self.query_one(Content).remove_class("centered-middle")

    def set_empty(self) -> None:
        self.reset()
        self.update("Empty")
        self.query_one(Content).add_class("centered-middle")

    def set_loading(self) -> None:
        self.reset()
        self.update("Loading...")
        self.query_one(Content).add_class("centered-middle")

    def reset(self) -> None:
        self.revisions = []
        self.current_revision = None
        self.update("")

    async def action_select_revision(self) -> None:
        if not self.revisions:
            return

        def fire_revision_event(revision: str) -> None:
            self.current_revision = revision
            self.post_message(self.RevisionSelected(revision, panel_type=self.TYPE))

        await self.app.push_screen(
            modals.RadioButtonsModal(
                "Select a revision to view",
                current=self.current_revision or "",
                options=self.revisions,
            ),
            fire_revision_event,
        )

    async def action_sync_panels(self) -> None:
        self.post_message(self.SyncPanelsRequest(self.TYPE))

    async def action_select_diff_type(self) -> None:
        def fire_diff_type_event(diff_type: str) -> None:
            self.current_diff_type = diff_type
            self.post_message(
                self.DIffTypeSelected(DiffType(diff_type), panel_type=self.TYPE)
            )

        await self.app.push_screen(
            modals.RadioButtonsModal(
                "Select a differ",
                current=self.current_diff_type or "",
                options=self.diff_types,
            ),
            fire_diff_type_event,
        )


TEXT_PANEL_BINDINGS: list[Binding | tuple[str, str] | tuple[str, str, str]] = [
    Binding("r,к", "select_revision", "Revisions", show=True),
    Binding("s,ы,і", "sync_panels", "Sync", show=True),
]


class LeftPanel(Panel):
    TYPE = PanelType.LEFT
    BINDINGS = TEXT_PANEL_BINDINGS


class MiddlePanel(Panel):
    TYPE = PanelType.MIDDLE
    BINDINGS = [
        Binding("d,в", "select_diff_type", "Diff Type", show=True),
    ]


class RightPanel(Panel):
    TYPE = PanelType.RIGHT
    BINDINGS = TEXT_PANEL_BINDINGS
