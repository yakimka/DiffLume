import difflib
from dataclasses import dataclass
from enum import Enum


class DiffType(Enum):
    NDIFF = "ndiff"


class HighlightType(Enum):
    ADDED = "added"
    REMOVED = "removed"
    EXPLANATION = "explanation"


class Ndiff:
    def __call__(self, text: str, text_to_compare: str) -> str:
        diff = difflib.ndiff(
            text.splitlines(),
            text_to_compare.splitlines(),
        )
        return "\n".join(line.rstrip() for line in diff)

    def highlight_regexp(self) -> dict[HighlightType, str]:
        return {
            HighlightType.ADDED: r"(^|\n)\+.*",
            HighlightType.REMOVED: r"(^|\n)-.*",
            HighlightType.EXPLANATION: r"(^|\n)\?.*",
        }


diff_func_mapping = {
    DiffType.NDIFF: Ndiff(),
}


@dataclass(kw_only=True)
class DiffResult:
    text: str
    highlight_regexp: dict[HighlightType, str]


def create_diff(text: str, text_to_compare: str, diff_type: DiffType) -> DiffResult:
    differ = diff_func_mapping[diff_type]
    text = differ(text, text_to_compare)
    return DiffResult(
        text=text,
        highlight_regexp=differ.highlight_regexp(),
    )
