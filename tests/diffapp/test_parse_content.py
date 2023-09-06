import pytest

from difflume.diffapp.modules import TextType, parse_content


@pytest.mark.parametrize("text", ["", " ", "  ", '{"key": "value"', "some\ntext"])
def test_parse_plain_text(text: str):
    result = parse_content(text)

    assert result.text == text
    assert result.text_type == TextType.PLAIN


@pytest.mark.parametrize(
    "text,expected",
    [
        ("{}", "{}"),
        ("[ ]", "[]"),
        ('{"key": "value"}', '{\n  "key": "value"\n}'),
    ],
)
def test_parse_json(text: str, expected: str):
    result = parse_content(text)

    assert result.text == expected
    assert result.text_type == TextType.JSON


def test_sort_keys_and_indent_when_parsing_json():
    text = '{"key": "value", "another_key": "another_value"}'
    expected = '{\n  "another_key": "another_value",\n  "key": "value"\n}'

    result = parse_content(text)

    assert result.text == expected
    assert result.text_type == TextType.JSON
