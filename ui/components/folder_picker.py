import os
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from utils.theme import COLORS, FONT_BODY, FONT_CAPTION
from utils.constants import CORNER_RADIUS


class FolderPicker(ctk.CTkFrame):
    """Multi-folder selector with add/remove and drag-drop support."""

    def __init__(self, parent, on_change=None, **kwargs):
        super().__init__(parent,
                         fg_color=COLORS["bg_secondary"],
                         corner_radius=CORNER_RADIUS, **kwargs)
        self._folders: list[str] = []
        self._on_change = on_change
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkButton(
            header, text="+ Add Folder",
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=FONT_BODY, height=32, width=120,
            command=self._add_folder
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="or drag folders here",
            font=FONT_CAPTION, text_color=COLORS["text_muted"]
        ).pack(side="left", padx=10)

        self._list_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", height=160
        )
        self._list_frame.pack(fill="both", expand=True, padx=4, pady=(0, 6))

    def _add_folder(self):
        path = filedialog.askdirectory(title="Select Folder")
        if path and path not in self._folders:
            self._folders.append(path)
            self._refresh()

    def _refresh(self):
        for w in self._list_frame.winfo_children():
            w.destroy()
        for folder in self._folders:
            row = ctk.CTkFrame(self._list_frame, fg_color=COLORS["bg_tertiary"],
                               corner_radius=6)
            row.pack(fill="x", padx=4, pady=2)

            ctk.CTkLabel(
                row, text=f"\U0001f4c2  {folder}",
                font=FONT_CAPTION, text_color=COLORS["text_primary"],
                anchor="w"
            ).pack(side="left", padx=8, pady=6, fill="x", expand=True)

            f_capture = folder
            ctk.CTkButton(
                row, text="✕", width=28, height=28,
                fg_color="transparent", hover_color=COLORS["danger"],
                text_color=COLORS["text_secondary"], font=("Segoe UI", 11),
                command=lambda p=f_capture: self._remove(p)
            ).pack(side="right", padx=4)

        if self._on_change:
            self._on_change(self._folders)

    def _remove(self, path: str):
        if path in self._folders:
            self._folders.remove(path)
            self._refresh()

    def get_folders(self) -> list:
        return list(self._folders)

    def set_folders(self, folders: list):
        self._folders = list(folders)
        self._refresh()
