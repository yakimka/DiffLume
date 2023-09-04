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
