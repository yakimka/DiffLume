from rich.console import RenderableType
from rich.highlighter import Highlighter, JSONHighlighter, ReprHighlighter
from rich.style import Style
from rich.text import Text
from textual.containers import VerticalScroll
from textual.widget import Widget

from difflume.diffapp.differ import DiffType, HighlightType, create_diff
from difflume.diffapp.modules import Module, TextType


class PanelView(VerticalScroll):
    pass


def get_highlighter(text_type: TextType) -> Highlighter:
    if text_type is TextType.JSON:
        return JSONHighlighter()
    return ReprHighlighter()


class PanelContent(Widget, inherit_bindings=False):
    DEFAULT_CSS = """
    PanelContent {
        height: auto;
    }
    """

    def _set_waiting_style(self) -> None:
        self.add_class("centered-middle")

    def _remove_waiting_style(self) -> None:
        self.remove_class("centered-middle")


class ModuleWidget(PanelContent):
    _module: Module | None

    def __init__(
        self,
        module: Module | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.module = module

    @property
    def module(self) -> Module:
        return self._module or None

    @module.setter
    def module(self, module: Module) -> None:
        self._module = module

    def render(self) -> RenderableType:
        if not self.module:
            self._set_waiting_style()
            return Text("Empty")
        if not self.module.ready():
            self._set_waiting_style()
            return Text("Loading...")
        left_highlighter = get_highlighter(self.module.content.text_type)
        left_text = self.module.content.text
        self._remove_waiting_style()
        return left_highlighter(Text(left_text))

    def update(self, module: Module | None) -> None:
        self.module = module
        self.refresh(layout=True)


DIFF_COLORS = {
    HighlightType.ADDED: "dark_green",
    HighlightType.REMOVED: "red",
    HighlightType.EXPLANATION: "bright_black",
}


class DiffWidget(PanelContent):
    _left_module: Module | None
    _right_module: Module | None

    def __init__(
        self,
        left_module: Module | None = None,
        right_module: Module | None = None,
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
    def left_module(self) -> Module:
        return self._left_module or None

    @left_module.setter
    def left_module(self, left_module: Module) -> None:
        self._left_module = left_module

    @property
    def right_module(self) -> Module:
        return self._right_module or None

    @right_module.setter
    def right_module(self, right_module: Module) -> None:
        self._right_module = right_module

    def render(self) -> RenderableType:
        if not self.left_module or not self.right_module:
            self._set_waiting_style()
            return Text("")
        if not self.left_module.ready() or not self.right_module.ready():
            self._set_waiting_style()
            return Text("Loading...")

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
        self._remove_waiting_style()
        return diff_highlighted

    def update(self, left_module: Module, right_module: Module) -> None:
        self.left_module = left_module
        self.right_module = right_module
        self.refresh(layout=True)
