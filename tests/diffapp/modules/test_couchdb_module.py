import json

import httpx
import pytest

from difflume.diffapp.modules import (
    Content,
    CouchDBModule,
    ReadError,
    RevisionNotFoundError,
    TextType,
)

pytestmark = pytest.mark.usefixtures("couchdb_server")


@pytest.fixture()
async def client() -> httpx.AsyncClient:
    async with httpx.AsyncClient(timeout=1) as client:
        yield client


@pytest.fixture()
def couchdb_module_maker(document_url, client, couchdb_server):
    def maker(
        url: str = couchdb_server.url_for(document_url),  # noqa: B008
        client: httpx.AsyncClient = client,
    ) -> CouchDBModule:
        return CouchDBModule(url, client=client)

    return maker


@pytest.fixture()
def sut(couchdb_module_maker) -> CouchDBModule:
    return couchdb_module_maker()


@pytest.fixture()
def response_data_text(response_data) -> str:
    return json.dumps(response_data, indent=2, sort_keys=True, ensure_ascii=False)


async def test_read_document(sut: CouchDBModule, response_data_text):
    await sut.load()

    result = sut.get_content()

    assert result == Content(text=response_data_text, text_type=TextType.JSON)


async def test_can_load_revisions(sut: CouchDBModule):
    await sut.load()

    assert sut.revisions == ["7-abc", "6-def"]


async def test_read_content(sut: CouchDBModule, response_data_text):
    result = await sut.read_content()

    assert result == Content(text=response_data_text, text_type=TextType.JSON)


async def test_raise_error_if_cant_read_content(sut: CouchDBModule, couchdb_server):
    couchdb_server.clear_all_handlers()

    with pytest.raises(ReadError, match="Could not read URL"):
        await sut.read_content()


async def test_read_revisions(sut: CouchDBModule):
    result = await sut.read_revisions()

    assert result == ["7-abc", "6-def"]


async def test_raise_error_if_cant_load_revisions(sut: CouchDBModule, couchdb_server):
    couchdb_server.clear_all_handlers()

    with pytest.raises(ReadError, match="Could not read revision"):
        await sut.read_revisions()


async def test_save_latest_revision_when_load(
    sut: CouchDBModule, couchdb_server, response_data_text
):
    await sut.load()
    couchdb_server.clear_all_handlers()  # to be sure that we don't load content again

    result = sut.get_content("7-abc")

    assert result == Content(text=response_data_text, text_type=TextType.JSON)


async def test_get_content_return_latest_revision(sut: CouchDBModule, couchdb_server):
    await sut.load()
    couchdb_server.clear_all_handlers()  # to be sure that we don't load content again

    call_wo_revision = sut.get_content()
    call_latest_revision = sut.get_content("7-abc")

    assert call_wo_revision == call_latest_revision


async def test_load_only_latest_revision(sut: CouchDBModule):
    await sut.load()

    with pytest.raises(RevisionNotFoundError, match="Could not find revision"):
        sut.get_content("6-def")


async def test_load_specific_revision(sut: CouchDBModule, response_data_text):
    await sut.load()
    await sut.load_revision("6-def")

    result = sut.get_content("6-def")

    assert result == Content(
        text=response_data_text.replace("7-abc", "6-def"), text_type=TextType.JSON
    )


async def test_cant_load_missing_revisions(sut: CouchDBModule, couchdb_server):
    await sut.load()
    couchdb_server.clear_all_handlers()

    with pytest.raises(ReadError, match="Could not read revision"):
        await sut.load_revision("6-def")


async def test_dont_load_loaded_revision(sut: CouchDBModule, couchdb_server):
    await sut.load()
    await sut.load_revision("6-def")
    couchdb_server.clear_all_handlers()

    await sut.load_revision("6-def")  # dont raise error


async def test_rewrite_futon_url(
    couchdb_module_maker, couchdb_server, response_data_text
):
    sut = couchdb_module_maker(
        couchdb_server.url_for("/_utils/document.html?collection/my_id")
    )
    await sut.load()

    result = sut.get_content()

    assert result == Content(text=response_data_text, text_type=TextType.JSON)


async def test_rewrite_futon_url_with_revision(
    couchdb_module_maker, couchdb_server, response_data_text
):
    sut = couchdb_module_maker(
        couchdb_server.url_for("/_utils/document.html?collection/my_id@6-def")
    )
    await sut.load()

    result = sut.get_content()

    assert result == Content(
        text=response_data_text.replace("7-abc", "6-def"), text_type=TextType.JSON
    )


async def test_rewrite_fauxton_url(
    couchdb_module_maker, couchdb_server, response_data_text
):
    sut = couchdb_module_maker(
        couchdb_server.url_for("/_utils/#database/collection/my_id")
    )
    await sut.load()

    result = sut.get_content()

    assert result == Content(text=response_data_text, text_type=TextType.JSON)
