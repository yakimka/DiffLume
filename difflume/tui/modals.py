from __future__ import annotations

import os
from typing import Generator

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import DirectoryTree, Footer

from difflume.diffapp.modules import FSModule


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

    async def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        new_module = FSModule(str(event.path))
        self.dismiss(new_module)
