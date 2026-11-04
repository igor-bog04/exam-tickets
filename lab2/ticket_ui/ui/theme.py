"""Палитра и шрифты интерфейса. Каждый цвет — пара (светлая тема, тёмная тема)."""

from __future__ import annotations

import customtkinter as ctk

BG = ("#F3F4F8", "#121318")
CARD = ("#FFFFFF", "#1C1D24")
CARD_BORDER = ("#E5E7EB", "#2A2C35")
FIELD = ("#F3F4F6", "#262833")
FIELD_HOVER = ("#E5E7EB", "#30323F")
TEXT = ("#111827", "#F3F4F6")
MUTED = ("#6B7280", "#9CA3AF")
ACCENT = ("#4F46E5", "#6366F1")
ACCENT_HOVER = ("#4338CA", "#4F46E5")
ACCENT_SOFT = ("#EEF2FF", "#272A4A")
ACCENT_TEXT = ("#4338CA", "#A5B4FC")
ON_ACCENT = "#FFFFFF"
ON_ACCENT_MUTED = "#C7D2FE"
WARNING_TEXT = ("#92400E", "#FBBF24")
WARNING_SOFT = ("#FEF3C7", "#3A2F12")
DANGER_TEXT = ("#B91C1C", "#F87171")
DANGER_SOFT = ("#FEE2E2", "#3B1C1C")
SUCCESS_TEXT = ("#047857", "#34D399")
DISABLED = ("#C7C9D9", "#3A3C4A")

FONT_FAMILY = "Segoe UI"


class Fonts:
    """Шрифты создаются после корневого окна — tkinter требует его наличия."""

    def __init__(self) -> None:
        self.hero = ctk.CTkFont(FONT_FAMILY, 30, "bold")
        self.title = ctk.CTkFont(FONT_FAMILY, 22, "bold")
        self.subtitle = ctk.CTkFont(FONT_FAMILY, 13)
        self.section = ctk.CTkFont(FONT_FAMILY, 15, "bold")
        self.label = ctk.CTkFont(FONT_FAMILY, 12, "bold")
        self.body = ctk.CTkFont(FONT_FAMILY, 14)
        self.small = ctk.CTkFont(FONT_FAMILY, 12)
        self.button = ctk.CTkFont(FONT_FAMILY, 15, "bold")
        self.stat = ctk.CTkFont(FONT_FAMILY, 22, "bold")


def center(window, width: int, height: int, parent=None) -> None:
    window.update_idletasks()
    if parent is not None:
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    else:
        x = (window.winfo_screenwidth() - width) // 2
        y = (window.winfo_screenheight() - height) // 3
    window.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")


def circle(master, text: str, size: int, fg_color, text_color, font) -> ctk.CTkFrame:
    """Круглый значок. CTkLabel со скруглением добавляет боковые отступы и получается овал."""
    frame = ctk.CTkFrame(master, width=size, height=size, corner_radius=size // 2, fg_color=fg_color)
    frame.grid_propagate(False)
    frame.pack_propagate(False)
    ctk.CTkLabel(frame, text=text, font=font, text_color=text_color, fg_color="transparent").place(
        relx=0.5, rely=0.5, anchor="center"
    )
    return frame


def card(master, **pack_options) -> ctk.CTkFrame:
    frame = ctk.CTkFrame(master, fg_color=CARD, corner_radius=16, border_width=1, border_color=CARD_BORDER)
    frame.pack(fill="x", **pack_options)
    return frame
