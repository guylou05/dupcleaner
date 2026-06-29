import tkinter as tk
import customtkinter as ctk
from utils.theme import COLORS, apply_theme, FONT_HEADING_LG, FONT_BODY, FONT_CAPTION
from utils.constants import (
    APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT,
    MIN_WIDTH, MIN_HEIGHT, SIDEBAR_WIDTH, TITLEBAR_HEIGHT
)
from db.database import get_setting, set_setting, init_db
from ui.sidebar import Sidebar
from ui.views.scan_view import ScanView
from ui.views.results_view import ResultsView
from ui.views.history_view import HistoryView
from ui.views.trash_view import TrashView
from ui.views.scheduler_view import SchedulerView
from ui.views.settings_view import SettingsView


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        apply_theme()
        self._setup_window()
        self._build_titlebar()
        self._build_layout()
        self._show_first_run_if_needed()
        self._restore_geometry()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_window(self):
        self.title(APP_NAME)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.configure(fg_color=COLORS["bg_primary"])

    def _build_titlebar(self):
        bar = ctk.CTkFrame(self, fg_color=COLORS["sidebar_bg"],
                            height=TITLEBAR_HEIGHT, corner_radius=0)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        ctk.CTkLabel(
            bar, text=f"\U0001f9f9  {APP_NAME}",
            font=("Segoe UI", 13, "bold"),
            text_color=COLORS["accent"]
        ).pack(side="left", padx=16, pady=8)

        ctk.CTkLabel(
            bar, text=f"v{APP_VERSION}",
            font=FONT_CAPTION, text_color=COLORS["text_muted"]
        ).pack(side="left")

    def _build_layout(self):
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_primary"], corner_radius=0)
        container.pack(fill="both", expand=True)

        # Sidebar is created first; it calls navigate("scan") during __init__.
        # _views is not set yet at that point, so navigate() guards with hasattr.
        self.sidebar = Sidebar(container, on_navigate=self.navigate)
        self.sidebar.pack(side="left", fill="y")

        self._content = ctk.CTkFrame(container, fg_color=COLORS["bg_primary"],
                                      corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        self._views = {
            "scan":      ScanView(self._content, self),
            "results":   ResultsView(self._content, self),
            "history":   HistoryView(self._content, self),
            "trash":     TrashView(self._content, self),
            "scheduler": SchedulerView(self._content, self),
            "settings":  SettingsView(self._content, self),
        }
        self._active_view: str | None = None
        # Now that _views exists, do the initial navigation.
        self.navigate("scan")

    def navigate(self, key: str):
        if not hasattr(self, '_views') or key not in self._views:
            return
        if self._active_view:
            self._views[self._active_view].pack_forget()
        self._active_view = key
        view = self._views[key]
        view.pack(fill="both", expand=True)
        if key == "history" and hasattr(view, "refresh"):
            view.refresh()
        if key == "trash" and hasattr(view, "refresh"):
            view.refresh()
        if hasattr(self, "sidebar"):
            self.sidebar.set_active(key)

    def show_results(self, groups: list, scan_history_id: int = None):
        import json
        from datetime import datetime

        if scan_history_id and groups:
            try:
                def _fi_dict(fi):
                    return {
                        "path": fi.path, "name": fi.name,
                        "size_bytes": fi.size_bytes,
                        "modified_at": fi.modified_at.isoformat() if fi.modified_at else None,
                        "extension": fi.extension,
                        "marked_for_delete": fi.marked_for_delete,
                        "is_recommended_keep": fi.is_recommended_keep,
                    }
                raw = [
                    {
                        "hash_value": g.hash_value,
                        "files": [_fi_dict(f) for f in g.files],
                        "total_size_bytes": g.total_size_bytes,
                        "wasted_bytes": g.wasted_bytes,
                        "group_type": g.group_type,
                        "similarity_score": g.similarity_score,
                    }
                    for g in groups
                ]
                from db.database import update_scan_history
                update_scan_history(
                    scan_history_id,
                    completed_at=datetime.now().isoformat(),
                    duplicate_groups=len(groups),
                    wasted_bytes=sum(g.wasted_bytes for g in groups),
                    results_json=json.dumps(raw),
                )
            except Exception:
                pass

        results_view: ResultsView = self._views["results"]
        results_view.load_results(groups, scan_history_id)
        self.navigate("results")

    def _show_first_run_if_needed(self):
        if get_setting("first_run", "true") == "true":
            self.after(500, self._show_welcome)

    def _show_welcome(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Welcome")
        modal.geometry("440x320")
        modal.configure(fg_color=COLORS["bg_primary"])
        modal.resizable(False, False)
        modal.grab_set()

        ctk.CTkLabel(
            modal, text=f"Welcome to {APP_NAME}!",
            font=FONT_HEADING_LG, text_color=COLORS["text_primary"]
        ).pack(pady=(28, 8))

        ctk.CTkLabel(
            modal,
            text="Let's find duplicate files wasting space on your computer.",
            font=FONT_BODY, text_color=COLORS["text_secondary"]
        ).pack(pady=4)

        steps = ctk.CTkFrame(modal, fg_color=COLORS["bg_secondary"], corner_radius=8)
        steps.pack(padx=32, pady=16, fill="x")
        for line in [
            "①  Click \"Add Folder\" to select where to scan",
            "②  Click \"Start Scan\"",
            "③  Review duplicates and free up space",
        ]:
            ctk.CTkLabel(steps, text=line, font=FONT_BODY,
                         text_color=COLORS["text_primary"], anchor="w"
                         ).pack(anchor="w", padx=16, pady=4)

        def on_start():
            set_setting("first_run", "false")
            modal.destroy()

        ctk.CTkButton(
            modal, text="Get Started", height=40, width=160,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=("Segoe UI", 13, "bold"),
            command=on_start
        ).pack(pady=8)

    def _restore_geometry(self):
        geo = get_setting("window_geometry", "")
        if geo:
            try:
                self.geometry(geo)
            except Exception:
                pass

    def _on_close(self):
        try:
            set_setting("window_geometry", self.geometry())
        except Exception:
            pass
        self.destroy()
