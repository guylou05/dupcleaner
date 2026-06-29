import customtkinter as ctk
from utils.theme import COLORS, FONT_BODY, FONT_BODY_BOLD, FONT_CAPTION
from utils.constants import APP_VERSION, SIDEBAR_WIDTH
from core.license import is_pro

NAV_ITEMS = [
    ("scan",      "\U0001f50d", "Scan"),
    ("results",   "\U0001f4cb", "Results"),
    ("history",   "\U0001f550", "History"),
    ("trash",     "\U0001f5d1", "Recovery Bin"),
    ("scheduler", "⏰", "Schedule"),
    ("settings",  "⚙", "Settings"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_navigate, **kwargs):
        super().__init__(parent,
                         fg_color=COLORS["sidebar_bg"],
                         width=SIDEBAR_WIDTH,
                         corner_radius=0, **kwargs)
        self.pack_propagate(False)
        self._on_navigate = on_navigate
        self._active = "scan"
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._build()

    def _build(self):
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(16, 8))
        ctk.CTkLabel(
            logo_frame, text="\U0001f9f9 DupeClear",
            font=("Segoe UI", 15, "bold"),
            text_color=COLORS["accent"]
        ).pack(padx=16, anchor="w")
        ctk.CTkLabel(
            logo_frame, text="Pro",
            font=("Segoe UI", 11),
            text_color=COLORS["text_muted"]
        ).pack(padx=16, anchor="w")

        ctk.CTkFrame(self, fg_color=COLORS["border"], height=1).pack(fill="x", pady=8)

        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8)

        for key, icon, label in NAV_ITEMS:
            btn = ctk.CTkButton(
                nav_frame,
                text=f"{icon}  {label}",
                anchor="w",
                font=FONT_BODY,
                height=40,
                fg_color="transparent",
                text_color=COLORS["text_secondary"],
                hover_color=COLORS["bg_tertiary"],
                corner_radius=6,
                command=lambda k=key: self._select(k)
            )
            btn.pack(fill="x", pady=2)
            self._buttons[key] = btn

        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)

        self._pro_badge = ctk.CTkFrame(self, fg_color=COLORS["accent_muted"],
                                        corner_radius=8)
        self._pro_badge.pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(
            self._pro_badge,
            text="⭐ Upgrade to Pro" if not is_pro() else "✔ Pro Activated",
            font=FONT_CAPTION,
            text_color=COLORS["text_primary"]
        ).pack(pady=8)

        ctk.CTkLabel(
            self, text=f"v{APP_VERSION}",
            font=FONT_CAPTION, text_color=COLORS["text_muted"]
        ).pack(pady=(0, 12))

        # Initial highlight — do NOT call _select here to avoid triggering
        # navigate() before App._views is populated.
        self._apply_highlight("scan")

    def _apply_highlight(self, key: str):
        """Update button styles only, no navigation side-effect."""
        self._active = key
        for k, btn in self._buttons.items():
            if k == key:
                btn.configure(
                    fg_color=COLORS["accent_muted"],
                    text_color=COLORS["text_primary"],
                    font=FONT_BODY_BOLD
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_secondary"],
                    font=FONT_BODY
                )

    def _select(self, key: str):
        """User clicked a nav button: update highlight AND trigger navigation."""
        self._apply_highlight(key)
        self._on_navigate(key)

    def set_active(self, key: str):
        """Called by App.navigate() to sync the sidebar highlight.
        Must NOT call _on_navigate — that would recurse infinitely."""
        self._apply_highlight(key)

    def refresh_pro_badge(self):
        for w in self._pro_badge.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._pro_badge,
            text="✔ Pro Activated" if is_pro() else "⭐ Upgrade to Pro",
            font=FONT_CAPTION,
            text_color=COLORS["text_primary"]
        ).pack(pady=8)
