import tkinter as tk
import math
from utils.theme import COLORS


class ProgressRing(tk.Canvas):
    """Animated circular progress indicator."""

    def __init__(self, parent, size: int = 120, line_width: int = 10, **kwargs):
        bg = kwargs.pop("bg", COLORS["bg_primary"])
        super().__init__(parent, width=size, height=size,
                         bg=bg, highlightthickness=0, **kwargs)
        self._size = size
        self._lw = line_width
        self._value = 0.0  # 0.0 to 1.0
        self._arc_id = None
        self._text_id = None
        self._draw()

    def set_value(self, value: float):
        self._value = max(0.0, min(1.0, value))
        self._draw()

    def _draw(self):
        self.delete("all")
        s = self._size
        lw = self._lw
        pad = lw + 4
        # track
        self.create_arc(pad, pad, s - pad, s - pad,
                        start=90, extent=360,
                        style="arc", outline=COLORS["border"], width=lw)
        # progress
        extent = -self._value * 360
        self.create_arc(pad, pad, s - pad, s - pad,
                        start=90, extent=extent,
                        style="arc", outline=COLORS["accent"], width=lw)
        # percentage text
        pct = int(self._value * 100)
        self.create_text(s // 2, s // 2, text=f"{pct}%",
                         fill=COLORS["text_primary"], font=("Segoe UI", 14, "bold"))
