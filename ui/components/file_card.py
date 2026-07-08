import io
import tkinter as tk
import customtkinter as ctk
from utils.theme import COLORS, FONT_BODY, FONT_BODY_BOLD, FONT_CAPTION, FONT_MONO
from utils.file_utils import format_size, safe_path_display, open_in_explorer
from utils.constants import THUMB_SIZE

try:
    from PIL import Image, ImageTk
    _PIL = True
except ImportError:
    _PIL = False

_ICON_MAP = {
    ".jpg": "\U0001f5bc", ".jpeg": "\U0001f5bc", ".png": "\U0001f5bc",
    ".gif": "\U0001f5bc", ".bmp": "\U0001f5bc", ".tiff": "\U0001f5bc",
    ".mp4": "\U0001f3ac", ".avi": "\U0001f3ac", ".mov": "\U0001f3ac",
    ".mp3": "\U0001f3b5", ".wav": "\U0001f3b5", ".flac": "\U0001f3b5",
    ".pdf": "\U0001f4cb", ".doc": "\U0001f4c4", ".docx": "\U0001f4c4",
    ".xls": "\U0001f4ca", ".xlsx": "\U0001f4ca",
    ".zip": "\U0001f4e6", ".rar": "\U0001f4e6", ".7z": "\U0001f4e6",
}


class FileCard(ctk.CTkFrame):
    """Single file row inside a duplicate group card."""

    def __init__(self, parent, file_info, on_check_change=None, on_preview=None, **kwargs):
        border_color = COLORS["success"] if file_info.is_recommended_keep else COLORS["border"]
        super().__init__(parent,
                         fg_color=COLORS["bg_secondary"],
                         border_color=border_color,
                         border_width=2 if file_info.is_recommended_keep else 0,
                         corner_radius=6, **kwargs)
        self._fi = file_info
        self._on_check = on_check_change
        self._on_preview = on_preview
        self._var = tk.BooleanVar(value=file_info.marked_for_delete)
        self._thumb_img = None
        self._build()

    def _build(self):
        # thumbnail column
        thumb_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_tertiary"],
                                   width=THUMB_SIZE + 8, height=THUMB_SIZE + 8,
                                   corner_radius=4)
        thumb_frame.pack(side="left", padx=8, pady=8)
        thumb_frame.pack_propagate(False)

        if self._fi.thumbnail and _PIL:
            try:
                img = Image.open(io.BytesIO(self._fi.thumbnail))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img,
                                       size=(THUMB_SIZE, THUMB_SIZE))
                lbl = ctk.CTkLabel(thumb_frame, image=ctk_img, text="")
                lbl.pack(expand=True)
                lbl.bind("<Button-1>", lambda e: self._on_preview and self._on_preview(self._fi))
                self._thumb_img = ctk_img
            except Exception:
                self._icon_label(thumb_frame)
        else:
            self._icon_label(thumb_frame)

        # info column
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=4, pady=6)

        top = ctk.CTkFrame(info, fg_color="transparent")
        top.pack(fill="x")

        icon = _ICON_MAP.get(self._fi.extension, "\U0001f4c4")
        ctk.CTkLabel(
            top, text=f"{icon}  {self._fi.name}",
            font=FONT_BODY_BOLD, text_color=COLORS["text_primary"], anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            top, text=format_size(self._fi.size_bytes),
            font=FONT_BODY, text_color=COLORS["text_secondary"]
        ).pack(side="right", padx=8)

        path_lbl = ctk.CTkLabel(
            info,
            text=safe_path_display(self._fi.path),
            font=FONT_MONO, text_color=COLORS["text_secondary"], anchor="w",
            cursor="hand2"
        )
        path_lbl.pack(fill="x", pady=1)
        path_lbl.bind("<Button-1>", lambda e: open_in_explorer(self._fi.path))

        meta = ctk.CTkFrame(info, fg_color="transparent")
        meta.pack(fill="x")
        mod = self._fi.modified_at.strftime("%B %d, %Y") if self._fi.modified_at else ""
        ctk.CTkLabel(
            meta, text=f"Modified: {mod}",
            font=FONT_CAPTION, text_color=COLORS["text_muted"]
        ).pack(side="left")

        if self._fi.is_recommended_keep:
            ctk.CTkLabel(
                meta, text="  \U0001f6e1 Keep this",
                font=FONT_CAPTION, text_color=COLORS["success"]
            ).pack(side="left", padx=8)

        # checkbox column — always shown, including on the recommended-keep
        # file, so the user can override which copy gets deleted.
        ctk.CTkCheckBox(
            self, text="", variable=self._var,
            width=24, height=24,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._toggled
        ).pack(side="right", padx=12)

    def _icon_label(self, parent):
        icon = _ICON_MAP.get(self._fi.extension, "\U0001f4c4")
        ctk.CTkLabel(parent, text=icon, font=("Segoe UI", 28)).pack(expand=True)

    def _toggled(self):
        self._fi.marked_for_delete = self._var.get()
        if self._on_check:
            self._on_check()

    def set_marked(self, val: bool):
        self._fi.marked_for_delete = val
        self._var.set(val)
