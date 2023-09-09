import pytest

from difflume.http.url import URLParts, build, parse


def test_parse_and_build():
    result = parse("scheme://netloc/path;parameters?query#fragment")

    assert build(result) == "scheme://netloc/path;parameters?query#fragment"


def test_parse_base_url():
    result = parse("scheme://netloc/path;parameters?query#fragment")

    assert result == URLParts(
        scheme="scheme",
        netloc="netloc",
        path="/path;parameters",
        params="",
        query="query",
        fragment="fragment",
    )


@pytest.mark.parametrize(
    "path,expected",
    [
        ("/path", "/path"),
        ("/path|with|pipes", "/path%7Cwith%7Cpipes"),
        ("/path/with/slashes", "/path/with/slashes"),
        ("/path+with+pluses", "/path+with+pluses"),
        ("/path with spaces", "/path%20with%20spaces"),
        ("/path_with_underscores", "/path_with_underscores"),
        ("/path-with-dashes", "/path-with-dashes"),
        ("/path\\with\\backslashes", "/path%5Cwith%5Cbackslashes"),
    ],
)
def test_quote_path(path, expected):
    result = build(
        URLParts(
            scheme="",
            netloc="",
            path=path,
            params="",
            query="",
            fragment="",
        ),
        quote=True,
    )

    assert result == expected


def test_add_query():
    result = parse("scheme://netloc/path;parameters?query#fragment").add_query(
        "key", "value"
    )

    assert result == URLParts(
        scheme="scheme",
        netloc="netloc",
        path="/path;parameters",
        params="",
        query="query&key=value",
        fragment="fragment",
    )
