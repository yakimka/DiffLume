from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget


class TextViewWidget(Widget):
    text = reactive(Text("Loading..."))

    def render(self) -> Text:
        return self.app.left_text


