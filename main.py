import sys
import time
import tkinter as tk
import customtkinter as ctk

from db.database import init_db
from utils.theme import COLORS, apply_theme
from utils.constants import APP_NAME, APP_VERSION


def show_splash() -> ctk.CTk:
    apply_theme()
    splash = ctk.CTk()
    splash.title("")
    splash.geometry("420x260")
    splash.resizable(False, False)
    splash.configure(fg_color=COLORS["bg_primary"])
    # Center on screen
    splash.update_idletasks()
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    x = (sw - 420) // 2
    y = (sh - 260) // 2
    splash.geometry(f"420x260+{x}+{y}")

    ctk.CTkLabel(
        splash, text="\U0001f9f9",
        font=("Segoe UI", 52)
    ).pack(pady=(36, 0))

    ctk.CTkLabel(
        splash, text=APP_NAME,
        font=("Segoe UI", 22, "bold"),
        text_color=COLORS["accent"]
    ).pack()

    dot_label = ctk.CTkLabel(
        splash, text="Loading",
        font=("Segoe UI", 12),
        text_color=COLORS["text_muted"]
    )
    dot_label.pack(pady=8)

    ctk.CTkLabel(
        splash, text=f"v{APP_VERSION}",
        font=("Segoe UI", 10),
        text_color=COLORS["text_muted"]
    ).pack(side="bottom", pady=10)

    dots = ["", ".", "..", "..."]
    _state = {"i": 0, "running": True}

    def _animate():
        if not _state["running"]:
            return
        dot_label.configure(text="Loading" + dots[_state["i"] % 4])
        _state["i"] += 1
        splash.after(400, _animate)

    _animate()
    splash.update()
    return splash, _state


def main():
    splash, splash_state = show_splash()

    # Init DB while splash is visible
    try:
        init_db()
    except Exception as e:
        print(f"DB init error: {e}", file=sys.stderr)

    # Keep splash visible for at least 1.8s
    splash.after(1800, lambda: None)
    splash.update()
    time.sleep(1.8)

    splash_state["running"] = False
    splash.destroy()

    from app import App
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
