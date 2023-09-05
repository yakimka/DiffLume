from __future__ import annotations

import contextlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from difflume.http import url
from httpx import AsyncClient, HTTPStatusError



class RevisionNotFoundError(Exception):
    pass


class TextType(Enum):
    PLAIN = "plain"
    JSON = "json"


@dataclass(kw_only=True, frozen=True)
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
        return self._content is not None

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
        if self.ready():
            return
        self.rewrite_inputs()
        self.content = await self.read_content()
        self.revisions = await self.retrieve_revisions()
        if self.revisions:
            self.revisions_content = {
                self.revisions[0]: self.content
            }

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


class CouchDBModule(Module):
    def __init__(self, url: str, *, client: AsyncClient) -> None:
        super().__init__()
        self._url = url
        self._client = client

    def rewrite_inputs(self) -> None:
        """
        Parse Fauxton admin URLs and rewrite them for retrieving JSON.

        Examples:
        From: `http://localhost:5984/_utils/document.html?collection/my_id`
        To: `http://localhost:5984/collection/my_id`
        ---
        From: `http://localhost:5984/_utils/document.html?collection/my_id@7-abc`
        To: `http://localhost:5984/collection/my_id?rev=7-abc`
        ---
        From: `http://localhost:5984/_utils/#database/collection/my_id`
        To: `http://localhost:5984/collection/my_id`
        """
        parts = url.parse(self._url)
        # ver 1.x (Futon)
        if parts.path.startswith("/_utils/document.html"):
            path, *rev = parts.query.split("@")
            parts.path = path
            parts.query = f"rev={rev[0]}" if rev else ""
            self._url = url.build(parts)
        # ver 2.x-3.x (Fauxton)
        elif parts.path == "/_utils/" and parts.fragment.startswith("database/"):
            parts.path = parts.fragment.removeprefix("database/")
            parts.fragment = ""
            self._url = url.build(parts)

    async def _read_text(self) -> str:
        res = await self._client.get(self._url, timeout=15)
        return res.text

    async def retrieve_revisions(self) -> list[str]:
        parts = url.parse(self._url)
        parts.query = f"{parts.query}&revs=true"
        res = await self._client.get(url.build(parts), timeout=15)
        revs_info = res.json().get("_revs_info", [])
        return [rev["rev"] for rev in revs_info if rev["status"] == "available"]

    async def read_revision(self, revision: str) -> Content:
        if revision in self.revisions_content:
            return self.revisions_content[revision]
        parts = url.parse(self._url)
        parts.query = f"{parts.query}&rev={revision}"

        res = await self._client.get(url.build(parts), timeout=15)
        try:
            res.raise_for_status()
        except HTTPStatusError as e:
            raise RevisionNotFoundError(revision) from e

        content = parse_content(res.text)
        self.revisions_content[revision] = content
        return content
