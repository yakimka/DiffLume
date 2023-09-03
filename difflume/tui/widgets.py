from rich.console import RenderableType
from rich.highlighter import Highlighter, JSONHighlighter, ReprHighlighter
from rich.style import Style
from rich.text import Text
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widget import Widget

from difflume.diffapp.differ import DiffType, HighlightType, create_diff
from difflume.diffapp.modules import FSModule, TextType


class PanelView(VerticalScroll):
    BINDINGS = [
        Binding("d", "toggle_class('Static', 'centered2')", "Center2 text", show=True),
    ]


def get_highlighter(text_type: TextType) -> Highlighter:
    if text_type is TextType.JSON:
        return JSONHighlighter()
    return ReprHighlighter()


class PanelContent(Widget, inherit_bindings=False):
    DEFAULT_CLASSES = "panel-content"


class ModuleWidget(PanelContent):
    DEFAULT_CSS = """
    ModuleWidget {
        height: auto;
    }
    """

    BINDINGS = [
        Binding("r", "toggle_class('Static', 'centered4')", "Center4 text", show=True),
    ]

    _module: FSModule | None

    def __init__(
        self,
        module: FSModule | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.module = module

    @property
    def module(self) -> FSModule:
        return self._module or None

    @module.setter
    def module(self, module: FSModule) -> None:
        self._module = module

    def render(self) -> RenderableType:
        left_highlighter = get_highlighter(self.module.content.text_type)
        left_text = self.module.content.text
        return left_highlighter(Text(left_text))

    def update(self, module: FSModule) -> None:
        self.module = module
        self.refresh(layout=True)


DIFF_COLORS = {
    HighlightType.ADDED: "dark_green",
    HighlightType.REMOVED: "red",
    HighlightType.EXPLANATION: "bright_black",
}


class DiffWidget(PanelContent):
    DEFAULT_CSS = """
    DiffWidget {
        height: auto;
    }
    """

    _left_module: FSModule | None
    _right_module: FSModule | None

    def __init__(
        self,
        left_module: FSModule | None = None,
        right_module: FSModule | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.left_module = left_module
        self.right_module = right_module

    @property
    def left_module(self) -> FSModule:
        return self._left_module or None

    @left_module.setter
    def left_module(self, left_module: FSModule) -> None:
        self._left_module = left_module

    @property
    def right_module(self) -> FSModule:
        return self._right_module or None

    @right_module.setter
    def right_module(self, right_module: FSModule) -> None:
        self._right_module = right_module

    def render(self) -> RenderableType:
        diff_result = create_diff(
            self.left_module.content.text,
            self.right_module.content.text,
            DiffType.NDIFF,
        )
        diff_highlighted = Text(diff_result.text)
        for highlight_type, regexp in diff_result.highlight_regexp.items():
            diff_highlighted.highlight_regex(
                regexp, Style(bgcolor=DIFF_COLORS[highlight_type])
            )
        return diff_highlighted

    def update(self, left_module: FSModule, right_module: FSModule) -> None:
        self.left_module = left_module
        self.right_module = right_module
        self.refresh(layout=True)
