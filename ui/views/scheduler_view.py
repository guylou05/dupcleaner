import json
import customtkinter as ctk
from utils.theme import COLORS, FONT_HEADING_LG, FONT_HEADING_SM, FONT_BODY, FONT_CAPTION
from utils.constants import CORNER_RADIUS
from ui.components.toast import show_toast
from core.license import is_pro
from core.scheduler import get_schedule_config, save_schedule_config, start_scheduler, stop_scheduler
from db.database import get_profiles


class SchedulerView(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], **kwargs)
        self._app = app
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=16)

        title_row = ctk.CTkFrame(scroll, fg_color="transparent")
        title_row.pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(title_row, text="Scheduled Scans",
                     font=FONT_HEADING_LG, text_color=COLORS["text_primary"]
                     ).pack(side="left")
        ctk.CTkLabel(title_row, text="  \U0001f512 Pro Feature",
                     font=FONT_CAPTION, text_color=COLORS["warning"]
                     ).pack(side="left", pady=6)

        if not is_pro():
            ctk.CTkLabel(
                scroll,
                text="Scheduled scans are available in DupeClear Pro.\nUpgrade in Settings to unlock this feature.",
                font=FONT_BODY, text_color=COLORS["text_muted"], justify="left"
            ).pack(anchor="w", pady=20)
            ctk.CTkButton(
                scroll, text="Upgrade to Pro →", width=160,
                fg_color=COLORS["warning"], hover_color="#b8860b",
                text_color="#000000",
                command=lambda: self._app.navigate("settings")
            ).pack(anchor="w")
            return

        config = get_schedule_config()

        card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_secondary"],
                             corner_radius=CORNER_RADIUS)
        card.pack(fill="x", pady=12)

        self._enabled_var = ctk.BooleanVar(value=config.get("enabled", False))
        ctk.CTkCheckBox(
            card, text="Enable scheduled scanning",
            variable=self._enabled_var,
            font=FONT_BODY, text_color=COLORS["text_primary"],
            fg_color=COLORS["accent"]
        ).pack(anchor="w", padx=16, pady=(16, 8))

        def row(parent, label, widget_factory):
            r = ctk.CTkFrame(parent, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(r, text=label, font=FONT_BODY,
                         text_color=COLORS["text_secondary"], width=160, anchor="w"
                         ).pack(side="left")
            widget_factory(r).pack(side="left")

        self._freq_var = ctk.StringVar(value=config.get("frequency", "Weekly").title())
        row(card, "Run every:", lambda p: ctk.CTkOptionMenu(
            p, values=["Daily", "Weekly", "Monthly"],
            variable=self._freq_var,
            fg_color=COLORS["bg_tertiary"], button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_secondary"], width=140
        ))

        days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        self._day_var = ctk.StringVar(value=config.get("day", "Sunday").title())
        row(card, "On:", lambda p: ctk.CTkOptionMenu(
            p, values=days,
            variable=self._day_var,
            fg_color=COLORS["bg_tertiary"], button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_secondary"], width=140
        ))

        times = [f"{h:02d}:00" for h in range(24)]
        self._time_var = ctk.StringVar(value=config.get("time", "02:00"))
        row(card, "At:", lambda p: ctk.CTkOptionMenu(
            p, values=times,
            variable=self._time_var,
            fg_color=COLORS["bg_tertiary"], button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_secondary"], width=120
        ))

        profiles = [p["name"] for p in get_profiles()]
        self._profile_var = ctk.StringVar(value=config.get("profile", profiles[0] if profiles else ""))
        row(card, "Scan profile:", lambda p: ctk.CTkOptionMenu(
            p, values=profiles or ["No profiles"],
            variable=self._profile_var,
            fg_color=COLORS["bg_tertiary"], button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_secondary"], width=200
        ))

        ctk.CTkLabel(card, text="Action after scan:",
                     font=FONT_HEADING_SM, text_color=COLORS["text_primary"]
                     ).pack(anchor="w", padx=16, pady=(12, 4))
        self._action_var = ctk.StringVar(value=config.get("action", "notify"))
        for val, label in [("notify", "Just notify me of results"),
                           ("auto_delete", "Auto-delete using Smart Select")]:
            ctk.CTkRadioButton(
                card, text=label, value=val, variable=self._action_var,
                font=FONT_BODY, text_color=COLORS["text_secondary"],
                fg_color=COLORS["accent"]
            ).pack(anchor="w", padx=28, pady=2)

        ctk.CTkButton(
            card, text="Save Schedule", height=38, width=160,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._save
        ).pack(anchor="w", padx=16, pady=16)

    def _save(self):
        config = {
            "enabled":   self._enabled_var.get(),
            "frequency": self._freq_var.get().lower(),
            "day":       self._day_var.get().lower(),
            "time":      self._time_var.get(),
            "profile":   self._profile_var.get(),
            "action":    self._action_var.get(),
        }
        save_schedule_config(config)
        stop_scheduler()
        if config["enabled"]:
            start_scheduler(on_complete=self._on_scheduled_scan)
        show_toast(self, "Schedule saved.", "success")

    def _on_scheduled_scan(self, groups, scanned, errors):
        self.after(0, lambda: self._app.show_results(groups, None))
