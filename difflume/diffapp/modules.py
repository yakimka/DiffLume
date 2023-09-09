from __future__ import annotations

import contextlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from json import JSONDecodeError

from httpx import AsyncClient, HTTPError

from difflume.http import url


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


class RevisionNotFoundError(Exception):
    pass


class ReadError(Exception):
    pass


class Module(ABC):
    _content: Content | None

    def __init__(self) -> None:
        self.revisions: list[str] = []
        self.revisions_content: dict[str, Content] = {}

    def get_content(self, revision: str | None = None) -> Content:
        if revision is None:
            revision = "latest"
        try:
            return self.revisions_content[revision]
        except KeyError:
            raise RevisionNotFoundError(f"Could not find revision {revision}") from None

    def ready(self) -> bool:
        return bool(self.revisions_content)

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
        content = await self.read_content()
        self.revisions = await self.read_revisions()
        self.revisions_content["latest"] = content
        if self.revisions:
            self.revisions_content[self.revisions[0]] = content

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
    async def read_revisions(self) -> list[str]:
        """
        Retrieve the revision numbers for the file.
        """

    @abstractmethod
    async def load_revision(self, revision: str) -> None:
        """
        Load the file at the given revision and cache its contents.
        """


class NoRevisionModuleMixin:
    async def read_revisions(self) -> list[str]:
        return []

    async def load_revision(self, revision: str) -> None:  # noqa: U100
        return None


class FSModule(NoRevisionModuleMixin, Module):
    def __init__(self, path: str) -> None:
        super().__init__()
        self._path = path

    async def _read_text(self) -> str:
        try:
            with open(self._path, "r") as f:
                return f.read()
        except (OSError, UnicodeDecodeError) as e:
            raise ReadError(f"Could not read file {self._path}") from e


class URLModule(NoRevisionModuleMixin, Module):
    def __init__(self, url: str, *, client: AsyncClient) -> None:
        super().__init__()
        self._url = url
        self._client = client

    async def _read_text(self) -> str:
        try:
            res = await self._client.get(self._url)
            res.raise_for_status()
            return res.text
        except HTTPError as e:
            raise ReadError(f"Could not read URL {self._url}") from e


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
        ---
        From: `http://localhost:5984/_utils/#/database/collection/my_id`
        To: `http://localhost:5984/collection/my_id`
        """
        parts = url.parse(self._url)
        if not parts.path.startswith("/_utils/"):
            return None

        # ver 1.x (Futon)
        if parts.path.startswith("/_utils/document.html"):
            path, *rev = parts.query.split("@")
            parts.path = path
            parts.query = f"rev={rev[0]}" if rev else ""
        # ver 2.x-3.x (Fauxton)
        elif parts.fragment.removeprefix("/").startswith("database/"):
            parts.path = parts.fragment.removeprefix("/").removeprefix("database/")
            parts.fragment = ""

        self._url = url.build(parts, quote=True)

    async def _read_text(self) -> str:
        try:
            res = await self._client.get(self._url)
            res.raise_for_status()
            return res.text
        except HTTPError as e:
            raise ReadError(f"Could not read URL {self._url}") from e

    async def read_revisions(self) -> list[str]:
        try:
            res = await self._client.get(self._url, params={"revs_info": "true"})
            res.raise_for_status()
            revs_info = res.json().get("_revs_info", [])
        except (HTTPError, JSONDecodeError) as e:
            raise ReadError("Could not read revisions") from e
        return [rev["rev"] for rev in revs_info if rev["status"] == "available"]

    async def load_revision(self, revision: str) -> None:
        if revision in self.revisions_content:
            return None
        try:
            res = await self._client.get(self._url, params={"rev": revision})
            res.raise_for_status()
        except HTTPError as e:
            raise ReadError(f"Could not read revision {revision}") from e

        self.revisions_content[revision] = parse_content(res.text)
