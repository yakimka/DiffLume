import pytest

from difflume.diffapp.differ import Ndiff


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
