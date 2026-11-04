"""Окно результата: номер билета и три вопроса. ESC закрывает только это окно."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ..models import IssuedTicket
from . import theme

WIDTH, HEIGHT = 620, 600


class ResultWindow(ctk.CTkToplevel):
    def __init__(self, master, issued: IssuedTicket, fonts: theme.Fonts, on_close: Callable[[], None]) -> None:
        super().__init__(master, fg_color=theme.BG)
        self._on_close = on_close
        record = issued.record

        self.title(f"Билет № {record.ticket_number}")
        theme.center(self, WIDTH, HEIGHT, parent=master)
        self.minsize(520, 480)
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", lambda _event: self.close())

        self._build_hero(issued, fonts)
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(16, 0))
        if record.repeat:
            self._build_repeat_badge(body, fonts)
        self._build_questions(body, issued, fonts)
        self._build_footer(fonts)

        # CTkToplevel на Windows появляется с задержкой — фокус и модальность после показа
        self.after(150, self._activate)

    def close(self) -> None:
        self.grab_release()
        self.destroy()
        self._on_close()

    def _activate(self) -> None:
        self.lift()
        self.focus_force()
        self.grab_set()

    def _build_hero(self, issued: IssuedTicket, fonts: theme.Fonts) -> None:
        hero = ctk.CTkFrame(self, fg_color=theme.ACCENT, corner_radius=0)
        hero.pack(fill="x")
        student = issued.record.student
        ctk.CTkLabel(hero, text="ВАШ БИЛЕТ", font=fonts.label, text_color=theme.ON_ACCENT_MUTED).pack(
            anchor="w", padx=28, pady=(24, 0)
        )
        ctk.CTkLabel(
            hero, text=f"Ваш билет № {issued.record.ticket_number}", font=fonts.hero, text_color=theme.ON_ACCENT
        ).pack(anchor="w", padx=28)
        ctk.CTkLabel(
            hero,
            text=f"{student.display_name}  ·  группа {student.group}",
            font=fonts.subtitle,
            text_color=theme.ON_ACCENT_MUTED,
        ).pack(anchor="w", padx=28, pady=(2, 22))

    @staticmethod
    def _build_repeat_badge(master, fonts: theme.Fonts) -> None:
        badge = ctk.CTkFrame(master, fg_color=theme.WARNING_SOFT, corner_radius=12)
        badge.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            badge,
            text="↻  Повторная выдача — номер взят из первой записи студента в журнале",
            font=fonts.small,
            text_color=theme.WARNING_TEXT,
            wraplength=WIDTH - 100,
            justify="left",
        ).pack(anchor="w", padx=14, pady=10)

    @staticmethod
    def _build_questions(master, issued: IssuedTicket, fonts: theme.Fonts) -> None:
        if issued.ticket is None:
            box = ctk.CTkFrame(master, fg_color=theme.DANGER_SOFT, corner_radius=12)
            box.pack(fill="x")
            ctk.CTkLabel(
                box,
                text="Вопросы этого билета не найдены в tickets.docx — билет удалён или повреждён.",
                font=fonts.body,
                text_color=theme.DANGER_TEXT,
                wraplength=WIDTH - 100,
                justify="left",
            ).pack(anchor="w", padx=16, pady=14)
            return

        for index, question in enumerate(issued.ticket.questions, start=1):
            row = theme.card(master, pady=(0, 10))
            row.grid_columnconfigure(1, weight=1)
            theme.circle(row, str(index), 36, theme.ACCENT_SOFT, theme.ACCENT_TEXT, fonts.section).grid(
                row=0, column=0, padx=(16, 14), pady=16, sticky="n"
            )
            ctk.CTkLabel(
                row,
                text=question,
                font=fonts.body,
                text_color=theme.TEXT,
                wraplength=WIDTH - 150,
                justify="left",
                anchor="w",
            ).grid(row=0, column=1, padx=(0, 16), pady=18, sticky="w")

    def _build_footer(self, fonts: theme.Fonts) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=16)
        ctk.CTkLabel(footer, text="Esc — вернуться к выбору", font=fonts.small, text_color=theme.MUTED).pack(side="left")
        ctk.CTkButton(
            footer,
            text="Готово",
            width=120,
            height=40,
            corner_radius=10,
            font=fonts.button,
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            command=self.close,
        ).pack(side="right")
