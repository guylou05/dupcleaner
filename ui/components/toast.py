import customtkinter as ctk
from utils.theme import COLORS, FONT_BODY


class Toast(ctk.CTkFrame):
    """Non-blocking notification that auto-dismisses."""

    def __init__(self, parent, message: str, kind: str = "info", duration_ms: int = 3000):
        color_map = {
            "info":    COLORS["accent"],
            "success": COLORS["success"],
            "error":   COLORS["danger"],
            "warning": COLORS["warning"],
        }
        fg = color_map.get(kind, COLORS["accent"])
        super().__init__(parent, fg_color=fg, corner_radius=8)
        self._duration = duration_ms

        ctk.CTkLabel(
            self, text=message, font=FONT_BODY,
            text_color="#FFFFFF"
        ).pack(padx=16, pady=8)

        self.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)
        self.lift()
        self.after(duration_ms, self.destroy)


def show_toast(parent, message: str, kind: str = "info", duration_ms: int = 3000):
    try:
        Toast(parent, message, kind, duration_ms)
    except Exception:
        pass
