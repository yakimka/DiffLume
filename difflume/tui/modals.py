# mypy: disable-error-code="override, misc"
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Generator

from textual.binding import Binding
from textual.containers import Center, ScrollableContainer
from textual.screen import ModalScreen
from textual.validation import URL
from textual.widgets import (
    Button,
    DirectoryTree,
    Footer,
    Input,
    Label,
    RadioButton,
    RadioSet,
)

from difflume.diffapp.modules import CouchDBModule, FSModule, URLModule

if TYPE_CHECKING:
    from textual import events
    from textual.app import ComposeResult

    from difflume.tui.app import DiffLume


class Modal(ModalScreen):
    BINDINGS = [Binding("escape,q,й", "pop_screen", "Close", show=True)]
    NAME = ""


class SelectFileModal(Modal):
    NAME = "File"

    def compose(self) -> Generator[ComposeResult, None, None]:
        yield DirectoryTree(self.get_path_for_tree_home(), id="select-file-dialog")
        yield Footer()

    def get_path_for_tree_home(self) -> str:
        if from_env := os.getenv("DIFF_LUME_FILE_TREE_HOME"):
            return from_env
        return os.getcwd()

    async def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        new_module = FSModule(str(event.path))
        self.dismiss(new_module)


class URLModalComposeMixin:
    def compose(self) -> Generator[ComposeResult, None, None]:
        yield Center(
            Input(placeholder="Enter URL", validators=[URL()]),
            id="select-url-dialog",
        )
        yield Footer()


class SelectURLModal(URLModalComposeMixin, Modal):
    app: DiffLume  # type: ignore[assignment]
    NAME = "URL"

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        new_module = URLModule(event.value, client=self.app.deps.http_client)
        self.dismiss(new_module)


class SelectCouchDBURLModal(URLModalComposeMixin, Modal):
    app: DiffLume  # type: ignore[assignment]
    NAME = "CouchDB URL"

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        new_module = CouchDBModule(event.value, client=self.app.deps.http_client)
        self.dismiss(new_module)


class OpenFileModal(Modal):
    CHILD_MODALS = [
        SelectURLModal,
        SelectFileModal,
        SelectCouchDBURLModal,
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


class RadioButtonsModal(Modal):
    def __init__(self, label: str, *, current: str, options: list[str]) -> None:
        super().__init__()
        self.label = label
        self.current = current
        self.options = options

    def compose(self) -> Generator[ComposeResult, None, None]:
        with ScrollableContainer(id="radio-buttons-dialog"):
            yield Label(self.label, id="radio-buttons-dialog-label")
            with RadioSet():
                for option in self.options:
                    yield RadioButton(option, value=self.current == option)
        yield Footer()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        self.dismiss(str(event.pressed.label))
