import json
import webbrowser
import customtkinter as ctk
from tkinter import filedialog
from utils.theme import COLORS, FONT_HEADING_LG, FONT_HEADING_SM, FONT_BODY, FONT_CAPTION
from utils.constants import APP_NAME, APP_VERSION, CORNER_RADIUS
from ui.components.toast import show_toast
from db.database import get_setting, set_setting
from core.license import is_pro, activate_license, deactivate_license


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], **kwargs)
        self._app = app
        self._build()

    def _section(self, parent, title: str) -> ctk.CTkFrame:
        ctk.CTkLabel(parent, text=title, font=FONT_HEADING_SM,
                     text_color=COLORS["text_secondary"]
                     ).pack(anchor="w", pady=(16, 4))
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_secondary"],
                             corner_radius=CORNER_RADIUS)
        card.pack(fill="x")
        return card

    def _row(self, parent, label: str, widget, pady: int = 10):
        r = ctk.CTkFrame(parent, fg_color="transparent")
        r.pack(fill="x", padx=16, pady=(pady, 0))
        ctk.CTkLabel(r, text=label, font=FONT_BODY,
                     text_color=COLORS["text_secondary"], width=200, anchor="w"
                     ).pack(side="left")
        widget(r).pack(side="left")
        return r

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(scroll, text="Settings",
                     font=FONT_HEADING_LG, text_color=COLORS["text_primary"]
                     ).pack(anchor="w", pady=(0, 8))

        # General
        gen = self._section(scroll, "General")
        self._theme_var = ctk.StringVar(value=get_setting("theme", "dark").title())
        self._row(gen, "Theme:", lambda p: ctk.CTkOptionMenu(
            p, values=["Dark", "Light", "System"],
            variable=self._theme_var,
            fg_color=COLORS["bg_tertiary"], button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_secondary"],
            width=140, command=self._apply_theme
        ))
        ctk.CTkFrame(gen, fg_color="transparent", height=12).pack()

        # Safe Delete
        sd = self._section(scroll, "Safe Delete")
        bin_path = get_setting("bin_path", "")
        if not bin_path:
            import os; from pathlib import Path
            bin_path = str(Path(os.getenv("APPDATA", Path.home())) / "DupeClearPro" / "RecoveryBin")
        self._bin_path_var = ctk.StringVar(value=bin_path)
        bpr = ctk.CTkFrame(sd, fg_color="transparent")
        bpr.pack(fill="x", padx=16, pady=10)
        ctk.CTkLabel(bpr, text="Recovery bin location:", font=FONT_BODY,
                     text_color=COLORS["text_secondary"], width=200, anchor="w"
                     ).pack(side="left")
        ctk.CTkLabel(bpr, textvariable=self._bin_path_var, font=("Consolas", 10),
                     text_color=COLORS["text_muted"]
                     ).pack(side="left", padx=4)
        ctk.CTkButton(bpr, text="Change", width=80, height=28,
                      fg_color=COLORS["bg_tertiary"],
                      command=self._change_bin
                      ).pack(side="left", padx=8)

        self._bin_days_var = ctk.StringVar(value=get_setting("auto_empty_bin_days", "30") + " days")
        self._row(sd, "Auto-empty bin after:", lambda p: ctk.CTkOptionMenu(
            p, values=["7 days","14 days","30 days","60 days","Never"],
            variable=self._bin_days_var,
            fg_color=COLORS["bg_tertiary"], button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_secondary"], width=140
        ))
        self._bin_size_var = ctk.StringVar(value=get_setting("max_bin_size_gb", "5") + " GB")
        self._row(sd, "Max bin size:", lambda p: ctk.CTkOptionMenu(
            p, values=["1 GB","2 GB","5 GB","10 GB","Unlimited"],
            variable=self._bin_size_var,
            fg_color=COLORS["bg_tertiary"], button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_secondary"], width=140
        ))
        ctk.CTkFrame(sd, fg_color="transparent", height=12).pack()

        # Smart Auto-Select
        sa = self._section(scroll, "Smart Auto-Select Rule")
        self._rule_var = ctk.StringVar(value={
            "newest": "Newest", "shortest_path": "Shortest Path",
            "primary_drive": "On Primary Drive"
        }.get(get_setting("auto_select_rule", "newest"), "Newest"))
        self._row(sa, "Keep file that is:", lambda p: ctk.CTkOptionMenu(
            p, values=["Newest","Shortest Path","On Primary Drive"],
            variable=self._rule_var,
            fg_color=COLORS["bg_tertiary"], button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_secondary"], width=180
        ))
        ctk.CTkFrame(sa, fg_color="transparent", height=12).pack()

        # Exclusions
        exc = self._section(scroll, "Excluded Folders")
        self._exclusions_frame = ctk.CTkFrame(exc, fg_color="transparent")
        self._exclusions_frame.pack(fill="x", padx=16, pady=8)
        self._refresh_exclusions()
        ctk.CTkButton(
            exc, text="+ Add Exclusion", height=28, width=140,
            fg_color=COLORS["bg_tertiary"], hover_color=COLORS["accent_muted"],
            font=FONT_CAPTION, command=self._add_exclusion
        ).pack(anchor="w", padx=16, pady=(0, 12))

        # License
        lic = self._section(scroll, "License")
        status_row = ctk.CTkFrame(lic, fg_color="transparent")
        status_row.pack(fill="x", padx=16, pady=(12, 4))
        dot_color = COLORS["success"] if is_pro() else COLORS["text_muted"]
        status_text = "Pro Plan" if is_pro() else "Free Plan"
        ctk.CTkLabel(status_row, text=f"●  {status_text}",
                     font=FONT_BODY_BOLD if is_pro() else FONT_BODY,
                     text_color=dot_color
                     ).pack(side="left")

        key_row = ctk.CTkFrame(lic, fg_color="transparent")
        key_row.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(key_row, text="License key:", font=FONT_BODY,
                     text_color=COLORS["text_secondary"], width=120, anchor="w"
                     ).pack(side="left")
        self._key_entry = ctk.CTkEntry(
            key_row, placeholder_text="DCP-XXXX-XXXX-XXXX-XXXX",
            width=260, fg_color=COLORS["bg_tertiary"],
            border_color=COLORS["border"]
        )
        self._key_entry.pack(side="left", padx=8)
        ctk.CTkButton(
            key_row, text="Activate", width=90, height=32,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._activate
        ).pack(side="left")

        buy_row = ctk.CTkFrame(lic, fg_color="transparent")
        buy_row.pack(fill="x", padx=16, pady=(4, 16))
        ctk.CTkButton(
            buy_row, text="Buy Pro — $24.99", height=36,
            fg_color=COLORS["warning"], hover_color="#b8860b",
            text_color="#000000", font=FONT_BODY_BOLD,
            command=lambda: webbrowser.open("https://dupeclearpro.com/buy")
        ).pack(side="left")

        # Save
        ctk.CTkButton(
            scroll, text="Save Settings", height=40, width=160,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=FONT_BODY_BOLD, command=self._save
        ).pack(anchor="w", pady=20)

        # About
        about = self._section(scroll, "About")
        ctk.CTkLabel(about,
                     text=f"{APP_NAME} v{APP_VERSION}\nBuilt with Python + CustomTkinter",
                     font=FONT_CAPTION, text_color=COLORS["text_muted"], justify="left"
                     ).pack(anchor="w", padx=16, pady=12)

    def _refresh_exclusions(self):
        for w in self._exclusions_frame.winfo_children():
            w.destroy()
        try:
            exclusions = json.loads(get_setting("excluded_folders", "[]"))
        except Exception:
            exclusions = []
        for folder in exclusions:
            r = ctk.CTkFrame(self._exclusions_frame, fg_color=COLORS["bg_tertiary"],
                              corner_radius=4)
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=folder, font=FONT_CAPTION,
                         text_color=COLORS["text_primary"]
                         ).pack(side="left", padx=8, pady=4)
            ctk.CTkButton(
                r, text="✕", width=24, height=24,
                fg_color="transparent", hover_color=COLORS["danger"],
                text_color=COLORS["text_secondary"],
                command=lambda f=folder: self._remove_exclusion(f)
            ).pack(side="right", padx=4)

    def _add_exclusion(self):
        path = filedialog.askdirectory(title="Select folder to exclude")
        if path:
            try:
                excl = json.loads(get_setting("excluded_folders", "[]"))
            except Exception:
                excl = []
            if path not in excl:
                excl.append(path)
                set_setting("excluded_folders", json.dumps(excl))
            self._refresh_exclusions()

    def _remove_exclusion(self, folder: str):
        try:
            excl = json.loads(get_setting("excluded_folders", "[]"))
        except Exception:
            excl = []
        if folder in excl:
            excl.remove(folder)
            set_setting("excluded_folders", json.dumps(excl))
        self._refresh_exclusions()

    def _change_bin(self):
        path = filedialog.askdirectory(title="Select Recovery Bin location")
        if path:
            self._bin_path_var.set(path)
            set_setting("bin_path", path)

    def _apply_theme(self, value: str):
        import customtkinter as ctk
        ctk.set_appearance_mode(value.lower())

    def _activate(self):
        key = self._key_entry.get().strip()
        if activate_license(key):
            show_toast(self, "Pro license activated! Restart to see all features.", "success")
            if hasattr(self._app, 'sidebar'):
                self._app.sidebar.refresh_pro_badge()
        else:
            show_toast(self, "Invalid license key.", "error")

    def _save(self):
        theme = self._theme_var.get().lower()
        set_setting("theme", theme)

        days_str = self._bin_days_var.get().replace(" days", "").replace("Never", "0")
        set_setting("auto_empty_bin_days", days_str)

        size_str = self._bin_size_var.get().replace(" GB", "").replace("Unlimited", "0")
        set_setting("max_bin_size_gb", size_str)

        rule_map = {"Newest": "newest", "Shortest Path": "shortest_path",
                    "On Primary Drive": "primary_drive"}
        set_setting("auto_select_rule", rule_map.get(self._rule_var.get(), "newest"))

        show_toast(self, "Settings saved.", "success")


FONT_BODY_BOLD = ("Segoe UI", 13, "bold")
