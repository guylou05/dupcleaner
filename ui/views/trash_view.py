import customtkinter as ctk
from utils.theme import COLORS, FONT_HEADING_LG, FONT_HEADING_SM, FONT_BODY, FONT_CAPTION
from utils.constants import CORNER_RADIUS
from utils.file_utils import format_size
from ui.components.toast import show_toast
from core.safe_delete import restore_file, permanently_delete, empty_bin, get_bin_size
from db.database import get_trash_items
import datetime


class TrashView(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], **kwargs)
        self._app = app
        self._build()

    def _build(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="\U0001f5d1  Recovery Bin",
            font=FONT_HEADING_LG, text_color=COLORS["text_primary"]
        ).pack(side="left", padx=20, pady=16)

        self._info_label = ctk.CTkLabel(
            header, text="",
            font=FONT_CAPTION, text_color=COLORS["text_secondary"]
        )
        self._info_label.pack(side="left", padx=12)

        ctk.CTkButton(
            header, text="Empty Bin", width=110, height=32,
            fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            font=FONT_CAPTION, command=self._empty_bin
        ).pack(side="right", padx=12, pady=16)

        ctk.CTkButton(
            header, text="Restore All", width=110, height=32,
            fg_color=COLORS["accent_muted"], hover_color=COLORS["accent"],
            font=FONT_CAPTION, command=self._restore_all
        ).pack(side="right", padx=4, pady=16)

        # List
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=16, pady=12)

        self.refresh()

    def refresh(self):
        for w in self._scroll.winfo_children():
            w.destroy()

        items = get_trash_items()
        total_size = get_bin_size()
        self._info_label.configure(
            text=f"{len(items)} files  •  {format_size(total_size)}"
        )

        if not items:
            ctk.CTkLabel(
                self._scroll,
                text="Recovery bin is empty.",
                font=FONT_BODY, text_color=COLORS["text_muted"]
            ).pack(pady=60)
            return

        for item in items:
            self._render_item(item)

    def _render_item(self, item):
        row = ctk.CTkFrame(self._scroll, fg_color=COLORS["bg_secondary"],
                            corner_radius=6)
        row.pack(fill="x", pady=3)

        try:
            dt = datetime.datetime.fromisoformat(item["deleted_at"])
            date_str = dt.strftime("%b %d")
        except Exception:
            date_str = "Unknown"

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=12, pady=8)

        ctk.CTkLabel(
            left,
            text=f"\U0001f4c4  {item['file_name']}  •  {format_size(item['size_bytes'])}  •  Deleted {date_str}",
            font=FONT_BODY, text_color=COLORS["text_primary"], anchor="w"
        ).pack(anchor="w")
        ctk.CTkLabel(
            left, text=f"Original: {item['original_path']}",
            font=("Consolas", 10), text_color=COLORS["text_muted"], anchor="w"
        ).pack(anchor="w")

        iid = item["id"]
        ctk.CTkButton(
            row, text="Restore", width=80, height=28,
            fg_color=COLORS["success"], hover_color="#2ea043",
            font=FONT_CAPTION,
            command=lambda i=iid: self._restore(i)
        ).pack(side="right", padx=8)
        ctk.CTkButton(
            row, text="Delete", width=70, height=28,
            fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            font=FONT_CAPTION,
            command=lambda i=iid: self._perm_delete(i)
        ).pack(side="right", padx=4)

    def _restore(self, item_id: int):
        ok, msg = restore_file(item_id)
        if ok:
            show_toast(self, f"Restored to {msg}", "success")
        else:
            show_toast(self, f"Restore failed: {msg}", "error")
        self.refresh()

    def _perm_delete(self, item_id: int):
        if permanently_delete(item_id):
            show_toast(self, "File permanently deleted.", "info")
        else:
            show_toast(self, "Could not delete file.", "error")
        self.refresh()

    def _restore_all(self):
        items = get_trash_items()
        ok_count = 0
        for item in items:
            ok, _ = restore_file(item["id"])
            if ok:
                ok_count += 1
        show_toast(self, f"Restored {ok_count} files.", "success")
        self.refresh()

    def _empty_bin(self):
        count, freed = empty_bin()
        show_toast(self, f"Bin emptied: {count} files, {format_size(freed)} freed.", "info")
        self.refresh()
