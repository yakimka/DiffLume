import json

import httpx
import pytest

from difflume.diffapp.modules import Content, ReadError, TextType, URLModule


@pytest.fixture()
def url() -> str:
    return "/test_url_module"


@pytest.fixture()
async def client() -> httpx.AsyncClient:
    async with httpx.AsyncClient(timeout=1) as client:
        yield client


@pytest.fixture()
def sut(url, client, httpserver) -> URLModule:
    return URLModule(httpserver.url_for(url), client=client)


async def test_read_text(sut: URLModule, url: str, httpserver):
    httpserver.make_endpoint(content="test\nfile", path=url)
    await sut.load()

    result = sut.get_content()

    assert result == Content(text="test\nfile", text_type=TextType.PLAIN)


async def test_read_json(sut: URLModule, url: str, httpserver):
    data = {
        "key": "value",
        "another_key": "another_value",
        "nested": {
            "key": "value",
            "another_key": "another_value",
        },
    }
    httpserver.make_endpoint(content=data, path=url)
    expected = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)

    await sut.load()

    result = sut.get_content()

    assert result == Content(text=expected, text_type=TextType.JSON)


async def test_raise_error_if_cant_reach_url(sut: URLModule, url: str, httpserver):
    httpserver.make_endpoint(content="Error", path=url, status=404)

    with pytest.raises(ReadError, match="Could not read URL"):
        await sut.load()


async def test_dont_load_loaded_content(sut: URLModule, url: str, httpserver):
    httpserver.make_endpoint(content="test file", path=url)
    await sut.load()

    httpserver.clear_all_handlers()
    httpserver.make_endpoint(content="new content", path=url)
    await sut.load()

    result = sut.get_content()

    assert result == Content(text="test file", text_type=TextType.PLAIN)
