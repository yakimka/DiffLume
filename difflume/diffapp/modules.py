import asyncio
import contextlib
import json
from dataclasses import dataclass
from enum import Enum


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


class FSModule:
    def __init__(self, path: str) -> None:
        self._path = path
        self.content: Content | None = None
        self.revisions: list[str] = []
        self.revisions_content: dict[str, Content] = {}

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

    async def read(self) -> None:
        await asyncio.sleep(3)
        self.content = await self.read_content()
        self.revisions = await self.retrieve_revisions()

    async def read_content(self) -> Content:
        """
        Read the file and return its contents.
        """
        return parse_content(await self._read_text())

    async def _read_text(self) -> str:
        """
        Read the file and return its contents (text).
        """
        with open(self._path, "r") as f:
            return f.read()

    async def retrieve_revisions(self) -> list[str]:
        """
        Retrieve the revision numbers for the file.
        """
        return []

    async def read_revision(self, revision: str) -> Content:
        """
        Read the file at the given revision and return its contents.
        """
        raise RevisionNotFoundError
