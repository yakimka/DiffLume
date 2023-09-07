import difflib
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Generator, Iterable


class DiffType(Enum):
    NDIFF = "ndiff"
    NDIFF_COLLAPSED = "ndiff_collapsed"


class HighlightType(Enum):
    ADDED = "added"
    REMOVED = "removed"
    EXPLANATION = "explanation"


class Ndiff:
    def __call__(self, text: str, text_to_compare: str) -> str:
        diff = self._make_diff(text, text_to_compare)
        return self._format_lines(diff)

    def _make_diff(self, text: str, text_to_compare: str) -> Iterable[str]:
        return difflib.ndiff(
            text.splitlines(),
            text_to_compare.splitlines(),
        )

    def _format_lines(self, lines: Iterable[str]) -> str:
        return "\n".join(line.rstrip() for line in lines)

    def highlight_regexp(self) -> dict[HighlightType, str]:
        return {
            HighlightType.ADDED: r"(^|\n)\+.*",
            HighlightType.REMOVED: r"(^|\n)-.*",
            HighlightType.EXPLANATION: r"(^|\n)\?.*",
        }


class NdiffCollapsed(Ndiff):
    def __init__(self, preserve_rows: int = 2, delimiter: str = "[...]") -> None:
        self.preserve_rows = preserve_rows
        self.delimiter = delimiter

    def __call__(self, text: str, text_to_compare: str) -> str:
        diff = self._make_diff(text, text_to_compare)
        return self._format_lines(self.collapse(diff))

    def collapse(self, lines: Iterable[str]) -> Generator[str, None, None]:
        lines_mapping, last_line_num = self._meaningful_lines(lines)
        return self._convert_lines_map_to_list_with_delimiters(
            lines_mapping, last_line=last_line_num
        )

    def _meaningful_lines(self, lines: Iterable[str]) -> tuple[dict[int, str], int]:
        prev_lines: deque[str] = deque(maxlen=self.preserve_rows)
        last_diff_distance = self.preserve_rows + 1
        result = {}
        last_line_num = 0
        for i, line in enumerate(lines):
            if line.startswith(("+", "-", "?")):
                for prev_i, prev in enumerate(prev_lines):
                    result[i - (self.preserve_rows - prev_i)] = prev
                result[i] = line
                last_diff_distance = 0
            else:
                last_diff_distance += 1
                if last_diff_distance <= self.preserve_rows:
                    result[i] = line
            prev_lines.append(line)
            last_line_num = i
        return result, last_line_num

    def _convert_lines_map_to_list_with_delimiters(
        self, lines_map: dict[int, str], last_line: int
    ) -> Generator[str, None, None]:
        prev_line = -1
        for i in range(last_line + 1):
            if i in lines_map:
                if i - 1 != prev_line:
                    yield self.delimiter
                yield lines_map[i]
                prev_line = i

        if lines_map and last_line not in lines_map:
            yield self.delimiter


diff_func_mapping = {
    DiffType.NDIFF: Ndiff(),
    DiffType.NDIFF_COLLAPSED: NdiffCollapsed(),
}


@dataclass(kw_only=True)
class DiffResult:
    text: str
    highlight_regexp: dict[HighlightType, str]


def create_diff(text: str, text_to_compare: str, diff_type: DiffType) -> DiffResult:
    differ = diff_func_mapping[diff_type]
    return DiffResult(
        text=differ(text, text_to_compare),
        highlight_regexp=differ.highlight_regexp(),
    )
