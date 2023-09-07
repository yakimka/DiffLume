import re

import pytest

from difflume.diffapp.differ import HighlightType, NdiffCollapsed


@pytest.fixture()
def sut():
    return NdiffCollapsed(preserve_rows=2, delimiter="[...]")


def test_delta(sut):
    text = """\
{
    "name": "John",
    "surname": "Doe",
    "birth": "1980-01-01",
    "sex": "male",
    "age": 30,
    "city": "New York",
    "children": 1,
    "hobbies": [
        "football",
        "programming",
        "reading"
    ]
}
"""
    text_to_compare = """\
{
    "name": "John",
    "surname": "Doe",
    "birth": "1980-01-01",
    "sex": "male",
    "age": 31,
    "city": "New York",
    "children": 1,
    "hobbies": [
        "football",
        "programming",
        "reading"
    ]
}
"""
    expected = """\
[...]
      "birth": "1980-01-01",
      "sex": "male",
-     "age": 30,
?             ^
+     "age": 31,
?             ^
      "city": "New York",
      "children": 1,
[...]"""

    result = sut(text, text_to_compare)

    assert result == expected


def test_delta_collapsed_in_middle(sut):
    text = """\
{
    "name": "John",
    "surname": "Doe",
    "birth": "1980-01-01",
    "sex": "male",
    "age": 30,
    "city": "New York",
    "children": 1,
    "hobbies": [
        "football",
        "programming",
        "reading"
    ]
}
"""
    text_to_compare = """\
{
    "name": "John",
    "surname": "Doe JR",
    "birth": "1980-01-01",
    "sex": "male",
    "age": 30,
    "city": "New York",
    "children": 1,
    "interests": [
        "football",
        "programming",
        "reading"
    ]
}
"""
    expected = """\
  {
      "name": "John",
-     "surname": "Doe",
+     "surname": "Doe JR",
?                    +++
      "birth": "1980-01-01",
      "sex": "male",
[...]
      "city": "New York",
      "children": 1,
-     "hobbies": [
+     "interests": [
          "football",
          "programming",
[...]"""

    result = sut(text, text_to_compare)

    assert result == expected


def test_empty_text(sut):
    text = ""
    text_to_compare = ""

    result = sut(text, text_to_compare)

    assert result == ""


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
