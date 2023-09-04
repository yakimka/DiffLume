import re

import pytest

from difflume.diffapp.differ import HighlightType, Ndiff


@pytest.fixture()
def sut():
    return Ndiff()


def test_delta(sut):
    text = """\
{
    "name": "John",
    "age": 30,
    "city": "New York"
}
"""
    text_to_compare = """\
{
    "name": "John",
    "age": 31,
    "city": "New York"
}
"""
    expected = """\
  {
      "name": "John",
-     "age": 30,
?             ^
+     "age": 31,
?             ^
      "city": "New York"
  }"""

    result = sut(text, text_to_compare)

    assert result == expected


@pytest.mark.parametrize(
    "type_,line",
    [
        (HighlightType.ADDED, '+     "age": 31,'),
        (HighlightType.ADDED, '\n+     "age": 31,'),
        (HighlightType.REMOVED, '-     "age": 30,'),
        (HighlightType.REMOVED, '\n-     "age": 30,'),
        (HighlightType.EXPLANATION, "?             ^"),
        (HighlightType.EXPLANATION, "\n?             ^"),
    ],
)
def test_highlight_regexp(sut, type_, line):
    regex = sut.highlight_regexp()[type_]

    assert re.search(regex, line)
