from __future__ import annotations

import asyncio
import contextlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import AsyncClient


class RevisionNotFoundError(Exception):
    pass


class TextType(Enum):
    PLAIN = "plain"
    JSON = "json"


@dataclass(kw_only=True)
class Content:
    text: str
    text_type: TextType


def parse_content(text: str) -> Content:
    text_type = TextType.PLAIN
    with contextlib.suppress(json.JSONDecodeError):
        text = json.dumps(
            json.loads(text), indent=2, sort_keys=True, ensure_ascii=False
        )
        text_type = TextType.JSON
    return Content(text=text, text_type=text_type)


class Module(ABC):
    _content: Content | None

    def __init__(self) -> None:
        self.revisions: list[str] = []
        self.revisions_content: dict[str, Content] = {}
        self._content = None

    @property
    def content(self) -> Content:
        if self._content is None:
            raise RuntimeError("Module content is not ready")
        return self._content

    @content.setter
    def content(self, content: Content) -> None:
        self._content = content

    def ready(self) -> bool:
        return self.content is not None

    def rewrite_inputs(self) -> None:
        """
        Modify the inputs as necessary. This is beneficial when some inputs aren't
        directly usable but can be converted into the correct format with a bit
        of processing.

        For instance, you might change a CouchDB admin URL that returns HTML
        into one that returns JSON.
        Example:
        From: `http://localhost:5984/_utils/document.html?collection/my_id`
        To: `http://localhost:5984/collection/my_id`
        """
        return None

    async def load(self) -> None:
        await asyncio.sleep(3)
        if self.ready():
            return
        self.rewrite_inputs()
        self.content = await self.read_content()
        self.revisions = await self.retrieve_revisions()

    async def read_content(self) -> Content:
        """
        Read the file and return its parsed content.
        """
        return parse_content(await self._read_text())

    @abstractmethod
    async def _read_text(self) -> str:
        """
        Read the file and return its contents (text).
        """

    @abstractmethod
    async def retrieve_revisions(self) -> list[str]:
        """
        Retrieve the revision numbers for the file.
        """

    @abstractmethod
    async def read_revision(self, revision: str) -> Content:
        """
        Read the file at the given revision and return its contents.
        """


class NoRevisionModule(Module, ABC):
    async def retrieve_revisions(self) -> list[str]:
        return []

    async def read_revision(self, revision: str) -> Content:  # noqa: U100
        raise RevisionNotFoundError


class FSModule(NoRevisionModule):
    def __init__(self, path: str) -> None:
        super().__init__()
        self._path = path

    async def _read_text(self) -> str:
        with open(self._path, "r") as f:
            return f.read()


class URLModule(NoRevisionModule):
    def __init__(self, url: str, *, client: AsyncClient) -> None:
        super().__init__()
        self._url = url
        self._client = client

    async def _read_text(self) -> str:
        res = await self._client.get(self._url, timeout=15)
        return res.text
