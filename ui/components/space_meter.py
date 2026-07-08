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
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=6)

        ctk.CTkLabel(
            inner, text="Potential Space Savings",
            font=FONT_CAPTION, text_color=COLORS["text_secondary"]
        ).pack(anchor="e")

        self._value_label = ctk.CTkLabel(
            inner, text="—",
            font=FONT_HEADING_MD, text_color=COLORS["text_muted"]
        )
        self._value_label.pack(anchor="e")

    def set_value(self, bytes_saved: int, total_bytes: int = 0):
        if self._anim_id:
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None

        if bytes_saved == 0:
            self._current_bytes = 0
            self._target_bytes = 0
            self._value_label.configure(text="—", text_color=COLORS["text_muted"])
            return

        self._target_bytes = bytes_saved
        self._animate()

    def _animate(self):
        step = max(1, (self._target_bytes - self._current_bytes) // 20)

        def tick():
            if self._current_bytes < self._target_bytes:
                self._current_bytes = min(self._current_bytes + step, self._target_bytes)
                self._value_label.configure(
                    text=format_size(self._current_bytes),
                    text_color=COLORS["success"]
                )
                self._anim_id = self.after(30, tick)
            else:
                self._value_label.configure(
                    text=format_size(self._target_bytes),
                    text_color=COLORS["success"]
                )

        tick()
