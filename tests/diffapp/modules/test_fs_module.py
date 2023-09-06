from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from difflume.diffapp.modules import Content, FSModule, ReadError, TextType

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture()
def file(tmp_path) -> Path:
    return tmp_path / "test_fs_modules.txt"


@pytest.fixture()
def sut(file) -> FSModule:
    return FSModule(str(file))


async def test_read_text(sut: FSModule, file: Path):
    file.write_text("test\nfile")
    await sut.load()

    result = sut.get_content()

    assert result == Content(text="test\nfile", text_type=TextType.PLAIN)


async def test_read_json_from_file(sut: FSModule, file: Path):
    data = {
        "key": "value",
        "another_key": "another_value",
        "nested": {
            "key": "value",
            "another_key": "another_value",
        },
    }
    file.write_text(json.dumps(data))
    expected = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)

    await sut.load()

    result = sut.get_content()

    assert result == Content(text=expected, text_type=TextType.JSON)


async def test_raise_error_if_cant_open_file(sut: FSModule, file: Path):
    assert file.exists() is False

    with pytest.raises(ReadError, match="Could not read file"):
        await sut.load()


async def test_raise_error_if_cant_decode_file(sut: FSModule, file: Path):
    file.write_bytes(b"\x89PNG\r\n\x1a\n")

    with pytest.raises(ReadError, match="Could not read file"):
        await sut.load()


async def test_dont_load_loaded_content(sut: FSModule, file: Path):
    file.write_text("test file")
    await sut.load()

    file.write_text("new\ncontent")
    await sut.load()

    result = sut.get_content()

    assert result == Content(text="test file", text_type=TextType.PLAIN)
