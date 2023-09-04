# mypy: disable-error-code="override, misc"
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Generator

from textual.binding import Binding
from textual.containers import Center, ScrollableContainer
from textual.screen import ModalScreen
from textual.validation import URL
from textual.widgets import Button, DirectoryTree, Footer, Input, Label

from difflume.diffapp.modules import FSModule, URLModule

if TYPE_CHECKING:
    from textual import events
    from textual.app import ComposeResult

    from difflume.tui.app import DiffLume


class Modal(ModalScreen):
    BINDINGS = [Binding("escape,q", "pop_screen", "Close", show=True)]
    NAME = ""


class SelectFileModal(Modal):
    NAME = "File"

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield DirectoryTree(os.getcwd(), id="select-file-dialog")
        yield Footer()

    async def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        new_module = FSModule(str(event.path))
        self.dismiss(new_module)


class SelectURLModal(Modal):
    app: DiffLume  # type: ignore[assignment]
    NAME = "URL"

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield Center(
            Input(placeholder="Enter URL", validators=[URL()]),
            id="select-url-dialog",
        )
        yield Footer()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        new_module = URLModule(event.value, client=self.app.deps.http_client)
        self.dismiss(new_module)


class OpenFileModal(Modal):
    CHILD_MODALS = [
        SelectURLModal,
        SelectFileModal,
    ]

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield ScrollableContainer(
            Label("Which type of file you would to open?", id="open-file-dialog-label"),
            *[
                Button(f"{i}. {child.NAME}", variant="primary", name=child.__name__)
                for i, child in enumerate(self.CHILD_MODALS, start=1)
            ],
            id="open-file-dialog",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.name)

    def on_key(self, event: events.Key) -> None:
        if event.key in [str(i) for i in range(1, 10)]:
            selected_modal = self.CHILD_MODALS[int(event.key) - 1]
            self.dismiss(selected_modal.__name__)
