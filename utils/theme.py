import customtkinter as ctk

COLORS_DARK = {
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

COLORS_LIGHT = {
    "bg_primary":     "#FFFFFF",
    "bg_secondary":   "#F6F8FA",
    "bg_tertiary":    "#EAEEF2",
    "accent":         "#0969DA",
    "accent_hover":   "#0860CA",
    "accent_muted":   "#DDF4FF",
    "danger":         "#CF222E",
    "danger_hover":   "#A40E26",
    "success":        "#1A7F37",
    "warning":        "#9A6700",
    "text_primary":   "#1F2328",
    "text_secondary": "#57606A",
    "text_muted":     "#8C959F",
    "border":         "#D0D7DE",
    "sidebar_bg":     "#F6F8FA",
}

# Mutable dict — mutated in-place by set_theme() so all imports stay in sync
COLORS: dict = dict(COLORS_DARK)

FONT_HEADING_LG  = ("Segoe UI", 24, "bold")
FONT_HEADING_MD  = ("Segoe UI", 18, "bold")
FONT_HEADING_SM  = ("Segoe UI", 14, "bold")
FONT_BODY        = ("Segoe UI", 13)
FONT_BODY_BOLD   = ("Segoe UI", 13, "bold")
FONT_CAPTION     = ("Segoe UI", 11)
FONT_MONO        = ("Consolas", 11)
FONT_MONO_SM     = ("Consolas", 10)


def set_theme(mode: str):
    """Switch palette in-place so all existing `from utils.theme import COLORS`
    references pick up the new values on the next widget rebuild."""
    palette = COLORS_LIGHT if mode == "light" else COLORS_DARK
    COLORS.clear()
    COLORS.update(palette)
    ctk.set_appearance_mode(mode)


def apply_theme():
    """Called once at startup (before DB is ready). Always starts dark."""
    ctk.set_default_color_theme("blue")
    set_theme("dark")


def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
