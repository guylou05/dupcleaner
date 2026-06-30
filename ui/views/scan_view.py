import json
import customtkinter as ctk
from utils.theme import COLORS, FONT_HEADING_LG, FONT_HEADING_SM, FONT_BODY, FONT_CAPTION
from utils.constants import CORNER_RADIUS
from ui.components.folder_picker import FolderPicker
from ui.components.progress_ring import ProgressRing
from ui.components.toast import show_toast
from db.models import ScanOptions
from db.database import get_profiles, save_profile, delete_profile, get_setting
from core.scanner import DuplicateScanner
from core.license import is_pro
from utils.file_utils import format_size

FILE_TYPE_OPTIONS = {
    "All Files":      [],
    "Images Only":    [".jpg",".jpeg",".png",".gif",".bmp",".tiff",".webp",".heic"],
    "Videos Only":    [".mp4",".avi",".mov",".mkv",".wmv",".flv"],
    "Documents Only": [".pdf",".doc",".docx",".xls",".xlsx",".ppt",".txt"],
}


class ScanView(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], **kwargs)
        self._app = app
        self._scanner: DuplicateScanner | None = None
        self._scanning = False
        self._files_total = 0
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(scroll, text="Scan for Duplicates",
                     font=FONT_HEADING_LG, text_color=COLORS["text_primary"]
                     ).pack(anchor="w", pady=(0, 16))

        # Folder picker
        ctk.CTkLabel(scroll, text="\U0001f4c1  Selected Folders",
                     font=FONT_HEADING_SM, text_color=COLORS["text_primary"]
                     ).pack(anchor="w", pady=(0, 6))
        self._folder_picker = FolderPicker(scroll, height=220)
        self._folder_picker.pack(fill="x", pady=(0, 16))

        # Auto-suggest Downloads on first use
        import os
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if os.path.isdir(downloads):
            if get_setting("first_run", "true") == "true":
                self._folder_picker.set_folders([downloads])

        # Options
        opts_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_secondary"],
                                   corner_radius=CORNER_RADIUS)
        opts_frame.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(opts_frame, text="Scan Options",
                     font=FONT_HEADING_SM, text_color=COLORS["text_primary"]
                     ).pack(anchor="w", padx=16, pady=(12, 6))

        row1 = ctk.CTkFrame(opts_frame, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(row1, text="File Types:", font=FONT_BODY,
                     text_color=COLORS["text_secondary"], width=120, anchor="w"
                     ).pack(side="left")
        self._type_var = ctk.StringVar(value="All Files")
        ctk.CTkOptionMenu(
            row1, values=list(FILE_TYPE_OPTIONS.keys()),
            variable=self._type_var,
            fg_color=COLORS["bg_tertiary"],
            button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_secondary"],
            width=200
        ).pack(side="left")

        row2 = ctk.CTkFrame(opts_frame, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(row2, text="Min File Size:", font=FONT_BODY,
                     text_color=COLORS["text_secondary"], width=120, anchor="w"
                     ).pack(side="left")
        self._min_size_var = ctk.StringVar(value="No Minimum")
        ctk.CTkOptionMenu(
            row2, values=["No Minimum", "1 KB", "10 KB", "100 KB", "1 MB", "10 MB"],
            variable=self._min_size_var,
            fg_color=COLORS["bg_tertiary"],
            button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_secondary"],
            width=200
        ).pack(side="left")

        self._hidden_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            opts_frame, text="Include hidden files",
            variable=self._hidden_var,
            font=FONT_BODY, text_color=COLORS["text_secondary"],
            fg_color=COLORS["accent"]
        ).pack(anchor="w", padx=16, pady=4)

        sim_row = ctk.CTkFrame(opts_frame, fg_color="transparent")
        sim_row.pack(anchor="w", padx=16, pady=(4, 12))
        self._sim_var = ctk.BooleanVar(value=False)
        self._sim_cb = ctk.CTkCheckBox(
            sim_row, text="Near-duplicate image detection",
            variable=self._sim_var,
            font=FONT_BODY, text_color=COLORS["text_secondary"],
            fg_color=COLORS["accent"],
            command=self._on_sim_toggle
        )
        self._sim_cb.pack(side="left")
        if not is_pro():
            ctk.CTkLabel(
                sim_row, text="  \U0001f512 Pro",
                font=FONT_CAPTION, text_color=COLORS["warning"]
            ).pack(side="left")

        # Profiles
        prof_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_secondary"],
                                   corner_radius=CORNER_RADIUS)
        prof_frame.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(prof_frame, text="Saved Profiles",
                     font=FONT_HEADING_SM, text_color=COLORS["text_primary"]
                     ).pack(anchor="w", padx=16, pady=(12, 6))
        pr = ctk.CTkFrame(prof_frame, fg_color="transparent")
        pr.pack(fill="x", padx=16, pady=(0, 12))
        self._profile_names = self._load_profile_names()
        self._profile_var = ctk.StringVar(value=self._profile_names[0] if self._profile_names else "")
        self._profile_menu = ctk.CTkOptionMenu(
            pr, values=self._profile_names or ["No profiles"],
            variable=self._profile_var,
            fg_color=COLORS["bg_tertiary"],
            button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_secondary"],
            width=180, command=self._load_profile
        )
        self._profile_menu.pack(side="left")
        ctk.CTkButton(
            pr, text="Save", width=70,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._save_profile
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            pr, text="Delete", width=70,
            fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            command=self._delete_profile
        ).pack(side="left")

        # Action area
        self._action_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._action_frame.pack(pady=16)
        self._start_btn = ctk.CTkButton(
            self._action_frame,
            text="  ▶  Start Scan",
            font=("Segoe UI", 14, "bold"),
            height=44, width=200,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._start_scan
        )
        self._start_btn.pack()

        # Progress area (hidden until scan starts)
        self._progress_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_secondary"],
                                             corner_radius=CORNER_RADIUS)
        self._status_label   = ctk.CTkLabel(self._progress_frame, text="",
                                             font=FONT_BODY, text_color=COLORS["text_primary"])
        self._file_label     = ctk.CTkLabel(self._progress_frame, text="",
                                             font=("Consolas", 10), text_color=COLORS["text_muted"])
        self._stats_label    = ctk.CTkLabel(self._progress_frame, text="",
                                             font=FONT_CAPTION, text_color=COLORS["text_secondary"])
        self._prog_bar       = ctk.CTkProgressBar(self._progress_frame, height=10,
                                                   fg_color=COLORS["bg_tertiary"],
                                                   progress_color=COLORS["accent"])

    def _on_sim_toggle(self):
        if self._sim_var.get() and not is_pro():
            self._sim_var.set(False)
            show_toast(self, "Near-duplicate detection requires Pro.", "warning")

    def _load_profile_names(self) -> list:
        return [p["name"] for p in get_profiles()]

    def _load_profile(self, name: str):
        for p in get_profiles():
            if p["name"] == name:
                folders = json.loads(p["folders"])
                self._folder_picker.set_folders(folders)
                break

    def _save_profile(self):
        from tkinter.simpledialog import askstring
        name = askstring("Save Profile", "Profile name:")
        if not name:
            return
        folders = self._folder_picker.get_folders()
        if not folders:
            show_toast(self, "Add at least one folder first.", "warning")
            return
        save_profile(name, folders, self._build_options().to_dict())
        self._profile_names = self._load_profile_names()
        self._profile_menu.configure(values=self._profile_names)
        self._profile_var.set(name)
        show_toast(self, f'Profile "{name}" saved.', "success")

    def _delete_profile(self):
        name = self._profile_var.get()
        if not name:
            return
        delete_profile(name)
        self._profile_names = self._load_profile_names()
        self._profile_menu.configure(values=self._profile_names or ["No profiles"])
        show_toast(self, f'Profile "{name}" deleted.', "info")

    def _build_options(self) -> ScanOptions:
        min_map = {"No Minimum": 0, "1 KB": 1, "10 KB": 10, "100 KB": 100, "1 MB": 1024, "10 MB": 10240}
        min_kb  = min_map.get(self._min_size_var.get(), 0)
        folders = self._folder_picker.get_folders()
        import json as _json
        exclude = _json.loads(get_setting("excluded_folders", "[]"))
        return ScanOptions(
            folders=folders,
            include_hidden=self._hidden_var.get(),
            min_file_size_kb=min_kb,
            file_type_filter=FILE_TYPE_OPTIONS.get(self._type_var.get(), []),
            exclude_folders=exclude,
            enable_image_similarity=self._sim_var.get(),
        )

    def _start_scan(self):
        folders = self._folder_picker.get_folders()
        if not folders:
            show_toast(self, "Please add at least one folder to scan.", "warning")
            return
        if self._scanning:
            return

        from db.database import set_setting
        set_setting("first_run", "false")

        opts = self._build_options()
        self._scanner = DuplicateScanner(opts)
        self._scanning = True
        self._show_progress()
        self._scanner.start(
            progress_callback=self._on_progress,
            complete_callback=self._on_complete,
            error_callback=self._on_error
        )

    def _show_progress(self):
        self._start_btn.pack_forget()
        self._progress_frame.pack(fill="x", pady=8)
        self._status_label.pack(pady=(12, 4))
        self._prog_bar.pack(fill="x", padx=16, pady=4)
        self._prog_bar.set(0)
        self._file_label.pack(pady=2)
        self._stats_label.pack(pady=(2, 4))

        cancel_btn = ctk.CTkButton(
            self._progress_frame, text="Cancel", width=100,
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["danger"],
            text_color=COLORS["text_primary"],
            command=self._cancel_scan
        )
        cancel_btn.pack(pady=(4, 12))
        self._cancel_btn = cancel_btn

    def _on_progress(self, scanned: int, total: int, groups_found: int, current_file: str):
        self.after(0, lambda: self._update_progress(scanned, total, groups_found, current_file))

    def _update_progress(self, scanned, total, groups_found, current_file):
        pct = scanned / max(total, 1)
        self._prog_bar.set(pct)
        self._status_label.configure(text=f"Scanning...  {int(pct*100)}%")
        self._file_label.configure(text=current_file[-70:] if current_file else "")
        self._stats_label.configure(
            text=f"Files scanned: {scanned:,} of {total:,}  •  Duplicates found: {groups_found}"
        )

    def _on_complete(self, groups, scanned, errors, cancelled, cap_hit=False, total_files=0):
        self.after(0, lambda: self._finish(groups, scanned, errors, cancelled, total_files))

    def _finish(self, groups, scanned, errors, cancelled, total_files=0):
        self._scanning = False
        self._progress_frame.pack_forget()
        self._start_btn.pack()
        if cancelled:
            show_toast(self, "Scan cancelled.", "warning")
            return
        total_wasted = sum(g.wasted_bytes for g in groups)
        if groups:
            msg = f"Found {len(groups)} duplicate groups — {format_size(total_wasted)} recoverable"
        else:
            msg = f"No duplicates found  ({total_files:,} files scanned)"
        if errors:
            msg += f"  •  {len(errors)} files inaccessible"
        show_toast(self, msg, "success" if groups else "info", duration_ms=5000)
        self._app.show_results(groups, scanned)

    def _on_error(self, exc):
        self.after(0, lambda: show_toast(self, f"Scan error: {exc}", "error"))
        self._scanning = False

    def _cancel_scan(self):
        if self._scanner:
            self._scanner.cancel()
