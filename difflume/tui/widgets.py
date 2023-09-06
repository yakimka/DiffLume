# mypy: disable-error-code="override, misc"
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Generator

from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widgets import Static

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
    BINDINGS = [
        Binding("r,к", "select_revision", "Revisions", show=True),
        Binding("s,ы,і", "sync_panels", "Sync", show=True),
    ]

    class RevisionSelected(Message):
        def __init__(self, revision: str, *, panel_type: PanelType) -> None:
            self.revision = revision
            self.panel_type = panel_type
            super().__init__()

    class SyncPanelsRequest(Message):
        def __init__(self, panel_type: PanelType) -> None:
            self.panel_type = panel_type
            super().__init__()

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
            modals.SelectRevisionModal(self.current_revision or "", self.revisions),
            fire_revision_event,
        )

    async def action_sync_panels(self) -> None:
        self.post_message(self.SyncPanelsRequest(self.TYPE))


class LeftPanel(Panel):
    TYPE = PanelType.LEFT


class MiddlePanel(Panel, inherit_bindings=False):
    TYPE = PanelType.MIDDLE


class RightPanel(Panel):
    TYPE = PanelType.RIGHT
