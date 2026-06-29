import tkinter as tk
import customtkinter as ctk
from utils.theme import COLORS, FONT_HEADING_MD, FONT_CAPTION
from utils.file_utils import format_size


class SpaceMeter(ctk.CTkFrame):
    """Animated disk space savings display."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_secondary"],
                         corner_radius=10, **kwargs)
        self._target_bytes = 0
        self._current_bytes = 0
        self._anim_id = None
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self, text="Potential Space Savings",
            font=FONT_CAPTION, text_color=COLORS["text_secondary"]
        ).pack(pady=(12, 2))

        self._value_label = ctk.CTkLabel(
            self, text="0 B",
            font=FONT_HEADING_MD, text_color=COLORS["success"]
        )
        self._value_label.pack()

        self._bar = ctk.CTkProgressBar(
            self, height=8,
            fg_color=COLORS["bg_tertiary"],
            progress_color=COLORS["success"]
        )
        self._bar.set(0)
        self._bar.pack(fill="x", padx=16, pady=(6, 12))

    def set_value(self, bytes_saved: int, total_bytes: int = 0):
        self._target_bytes = bytes_saved
        self._animate(total_bytes)

    def _animate(self, total_bytes: int):
        if self._anim_id:
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass

        step = max(1, (self._target_bytes - self._current_bytes) // 20)

        def tick():
            if self._current_bytes < self._target_bytes:
                self._current_bytes = min(self._current_bytes + step, self._target_bytes)
                self._value_label.configure(text=format_size(self._current_bytes))
                if total_bytes > 0:
                    self._bar.set(min(1.0, self._current_bytes / total_bytes))
                self._anim_id = self.after(30, tick)
            else:
                self._value_label.configure(text=format_size(self._target_bytes))

        tick()
