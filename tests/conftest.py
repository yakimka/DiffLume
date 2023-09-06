from __future__ import annotations

import pytest
from pytest_httpserver import HTTPServer as PytestHTTPServer


class HTTPServer:
    def __init__(self, httpserver: PytestHTTPServer):
        self._httpserver = httpserver

    def make_endpoint(
        self,
        *,
        content: dict | str,
        path: str,
        query: str | None = None,
        status: int = 200,
    ) -> HTTPServer:
        with_path = self._httpserver.expect_request(path, query_string=query)
        if isinstance(content, dict):
            with_path.respond_with_json(content, status=status)
        else:
            with_path.respond_with_data(content, status=status)
        return self

    def clear_all_handlers(self) -> None:
        self._httpserver.clear_all_handlers()

    def url_for(self, suffix: str) -> str:
        return self._httpserver.url_for(suffix)


@pytest.fixture()
def httpserver(httpserver: PytestHTTPServer):
    return HTTPServer(httpserver)


@pytest.fixture()
def response_data() -> dict:
    return {
        "_id": "my_id",
        "_rev": "7-abc",
        "key": "value",
        "another_key": "another_value",
        "nested": {
            "key": "value",
            "another_key": "another_value",
        },
    }


@pytest.fixture()
def document_url() -> str:
    return "/collection/my_id"


@pytest.fixture()
def couchdb_server(httpserver, response_data, document_url):
    httpserver.make_endpoint(
        content={
            "_revs_info": [
                {"rev": "7-abc", "status": "available"},
                {"rev": "6-def", "status": "available"},
                {"rev": "5-ghi", "status": "missing"},
            ],
            **response_data,
        },
        query="revs_info=true",
        path=document_url,
    )
    httpserver.make_endpoint(
        content=response_data, path=document_url, query="rev=7-abc"
    )
    httpserver.make_endpoint(
        content={
            **response_data,
            "_rev": "6-def",
        },
        path=document_url,
        query="rev=6-def",
    )
    httpserver.make_endpoint(content=response_data, path=document_url)

    return httpserver
