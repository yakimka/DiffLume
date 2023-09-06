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
