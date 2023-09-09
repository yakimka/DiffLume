from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import ParseResult
from urllib.parse import quote as url_quote
from urllib.parse import urlparse


@dataclass
class URLParts:
    scheme: str
    netloc: str
    path: str
    params: str
    query: str
    fragment: str

    def add_query(self, key: str, value: str) -> URLParts:
        self.query = "&".join([p for p in (self.query, f"{key}={value}") if p])
        return self


def parse(url: str) -> URLParts:
    result = urlparse(url)
    return URLParts(
        scheme=result.scheme,
        netloc=result.netloc,
        path=result.path,
        params=result.params,
        query=result.query,
        fragment=result.fragment,
    )


def build(parts: URLParts, *, quote: bool = False) -> str:
    path = parts.path
    if quote:
        path = url_quote(path, safe="/%+")
    return ParseResult(
        scheme=parts.scheme,
        netloc=parts.netloc,
        path=path,
        params=parts.params,
        query=parts.query,
        fragment=parts.fragment,
    ).geturl()
