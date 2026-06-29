import customtkinter as ctk

COLORS = {
    "bg_primary":     "#0D1117",
    "bg_secondary":   "#161B22",
    "bg_tertiary":    "#21262D",
    "accent":         "#2F81F7",
    "accent_hover":   "#388BFD",
    "accent_muted":   "#1F4B8E",
    "danger":         "#F85149",
    "danger_hover":   "#FF6B6B",
    "success":        "#3FB950",
    "warning":        "#D29922",
    "text_primary":   "#E6EDF3",
    "text_secondary": "#8B949E",
    "text_muted":     "#484F58",
    "border":         "#30363D",
    "sidebar_bg":     "#010409",
}

FONT_HEADING_LG  = ("Segoe UI", 24, "bold")
FONT_HEADING_MD  = ("Segoe UI", 18, "bold")
FONT_HEADING_SM  = ("Segoe UI", 14, "bold")
FONT_BODY        = ("Segoe UI", 13)
FONT_BODY_BOLD   = ("Segoe UI", 13, "bold")
FONT_CAPTION     = ("Segoe UI", 11)
FONT_MONO        = ("Consolas", 11)
FONT_MONO_SM     = ("Consolas", 10)


def apply_theme():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
