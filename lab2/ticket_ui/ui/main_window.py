"""Главное окно: выбор группы и студента, выдача билета, последние выдачи."""

from __future__ import annotations

from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from ..bootstrap import Sources
from ..errors import JournalError, JournalLockedError, SourceError
from ..models import ResultRecord, Student
from . import theme
from .result_window import ResultWindow

GROUP_PLACEHOLDER = "Выберите группу"
STUDENT_PLACEHOLDER = "Выберите студента"
STUDENT_WAITING = "Сначала выберите группу"
STUDENT_EMPTY = "В группе нет студентов"
RECENT_LIMIT = 5


class MainWindow(ctk.CTk):
    def __init__(self, load_sources: Callable[[], Sources], log_name: str) -> None:
        super().__init__(fg_color=theme.BG)
        self._load_sources = load_sources
        self._log_name = log_name
        self._sources: Sources | None = None
        self._students: dict[str, Student] = {}
        self._selected: Student | None = None

        self.title("Генератор экзаменационных билетов")
        theme.center(self, 640, 780)
        self.minsize(560, 680)
        self._fonts = theme.Fonts()

        self._build_header()
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        self._reload()

    # ── Загрузка ──────────────────────────────────────────────

    def _reload(self) -> None:
        for child in self._body.winfo_children():
            child.destroy()
        self._selected = None
        try:
            self._sources = self._load_sources()
        except SourceError as exc:
            self._sources = None
            self._build_error_state(str(exc))
            return
        self._build_form()
        self._build_stats()
        self._build_recent()
        self._build_problems()
        self._refresh_journal_views()

    # ── Построение интерфейса ─────────────────────────────────

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(22, 16))
        text = ctk.CTkFrame(header, fg_color="transparent")
        text.pack(side="left")
        ctk.CTkLabel(text, text="Экзаменационные билеты", font=self._fonts.title, text_color=theme.TEXT).pack(anchor="w")
        ctk.CTkLabel(
            text, text="Выберите группу и студента, чтобы выдать билет", font=self._fonts.subtitle, text_color=theme.MUTED
        ).pack(anchor="w")

        self._theme_switch = ctk.CTkSwitch(
            header,
            text="Тёмная тема",
            font=self._fonts.small,
            text_color=theme.MUTED,
            progress_color=theme.ACCENT,
            command=self._toggle_theme,
        )
        self._theme_switch.pack(side="right")
        if ctk.get_appearance_mode() == "Dark":
            self._theme_switch.select()

    def _build_error_state(self, message: str) -> None:
        box = theme.card(self._body, pady=(40, 0))
        theme.circle(box, "!", 56, theme.DANGER_SOFT, theme.DANGER_TEXT, self._fonts.title).pack(pady=(28, 12))
        ctk.CTkLabel(box, text="Не удалось загрузить данные", font=self._fonts.section, text_color=theme.TEXT).pack()
        ctk.CTkLabel(
            box, text=message, font=self._fonts.body, text_color=theme.MUTED, wraplength=460, justify="center"
        ).pack(padx=24, pady=(6, 4))
        ctk.CTkLabel(
            box,
            text="Положите students.xlsx и tickets.docx в папку data и нажмите «Повторить».",
            font=self._fonts.small,
            text_color=theme.MUTED,
            wraplength=460,
        ).pack(padx=24)
        self._primary_button(box, "Повторить", self._reload).pack(pady=(18, 28))

    def _build_form(self) -> None:
        form = theme.card(self._body)
        inner = ctk.CTkFrame(form, fg_color="transparent")
        inner.pack(fill="x", padx=22, pady=22)

        groups = self._sources.students.groups()
        self._field_label(inner, "ГРУППА")
        self._group_menu = self._option_menu(inner, groups, self._on_group_selected)
        self._group_menu.set(GROUP_PLACEHOLDER if groups else "В students.xlsx нет листов")
        if not groups:
            self._group_menu.configure(state="disabled")

        self._field_label(inner, "СТУДЕНТ", top=16)
        self._student_menu = self._option_menu(inner, [], self._on_student_selected)
        self._student_menu.set(STUDENT_WAITING)
        self._student_menu.configure(state="disabled")

        self._hint = ctk.CTkLabel(inner, text="", font=self._fonts.small, text_color=theme.WARNING_TEXT, anchor="w")
        self._hint.pack(fill="x", pady=(6, 0))

        self._generate_button = self._primary_button(inner, "Сгенерировать билет", self._on_generate)
        self._generate_button.configure(height=50)
        self._set_generate_enabled(False)
        self._generate_button.pack(fill="x", pady=(12, 0))

    def _build_stats(self) -> None:
        row = ctk.CTkFrame(self._body, fg_color="transparent")
        row.pack(fill="x", pady=14)
        self._stat_values: dict[str, ctk.CTkLabel] = {}
        stats = (
            ("tickets", "билетов в базе", len(self._sources.catalog.all())),
            ("groups", "групп", len(self._sources.students.groups())),
            ("issued", "выдано всего", "—"),
        )
        for column, (key, caption, value) in enumerate(stats):
            row.grid_columnconfigure(column, weight=1, uniform="stats")
            tile = ctk.CTkFrame(row, fg_color=theme.CARD, corner_radius=14, border_width=1, border_color=theme.CARD_BORDER)
            tile.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0 if column == 2 else 6))
            label = ctk.CTkLabel(tile, text=str(value), font=self._fonts.stat, text_color=theme.ACCENT_TEXT)
            label.pack(anchor="w", padx=16, pady=(12, 0))
            ctk.CTkLabel(tile, text=caption, font=self._fonts.small, text_color=theme.MUTED).pack(
                anchor="w", padx=16, pady=(0, 12)
            )
            self._stat_values[key] = label

    def _build_recent(self) -> None:
        box = ctk.CTkFrame(self._body, fg_color=theme.CARD, corner_radius=16, border_width=1, border_color=theme.CARD_BORDER)
        box.pack(fill="both", expand=True)
        ctk.CTkLabel(box, text="Последние выдачи", font=self._fonts.section, text_color=theme.TEXT).pack(
            anchor="w", padx=20, pady=(16, 6)
        )
        self._recent_list = ctk.CTkFrame(box, fg_color="transparent")
        self._recent_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _build_problems(self) -> None:
        problems = self._sources.catalog.problems
        if not problems:
            return
        banner = ctk.CTkFrame(self._body, fg_color=theme.WARNING_SOFT, corner_radius=12)
        banner.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(
            banner,
            text=f"⚠  При загрузке tickets.docx пропущено или исправлено: {len(problems)}. Подробности — в {self._log_name}",
            font=self._fonts.small,
            text_color=theme.WARNING_TEXT,
            wraplength=540,
            justify="left",
        ).pack(anchor="w", padx=14, pady=10)

    def _refresh_journal_views(self) -> None:
        for child in self._recent_list.winfo_children():
            child.destroy()
        try:
            records = self._sources.journal.records()
        except JournalError:
            self._stat_values["issued"].configure(text="?")
            self._muted_line(self._recent_list, "Журнал results.xlsx сейчас не читается")
            return

        self._stat_values["issued"].configure(text=str(len(records)))
        if not records:
            self._muted_line(self._recent_list, "Пока никому не выдано ни одного билета")
            return
        for record in reversed(records[-RECENT_LIMIT:]):
            self._recent_row(record)

    def _recent_row(self, record: ResultRecord) -> None:
        row = ctk.CTkFrame(self._recent_list, fg_color=theme.FIELD, corner_radius=10)
        row.pack(fill="x", pady=3)
        row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            row, text=f"№ {record.ticket_number}", width=56, font=self._fonts.label,
            fg_color=theme.ACCENT_SOFT, text_color=theme.ACCENT_TEXT, corner_radius=8,
        ).grid(row=0, column=0, rowspan=2, padx=10, pady=8)
        ctk.CTkLabel(
            row, text=record.student.display_name, font=self._fonts.body, text_color=theme.TEXT, anchor="w"
        ).grid(row=0, column=1, sticky="w", pady=(6, 0))
        when = record.issued_at.strftime("%d.%m.%Y %H:%M") if hasattr(record.issued_at, "strftime") else ""
        ctk.CTkLabel(
            row, text=f"{record.student.group}  ·  {when}", font=self._fonts.small, text_color=theme.MUTED, anchor="w"
        ).grid(row=1, column=1, sticky="w", pady=(0, 6))
        if record.repeat:
            ctk.CTkLabel(
                row, text="повтор", font=self._fonts.small, fg_color=theme.WARNING_SOFT,
                text_color=theme.WARNING_TEXT, corner_radius=8, width=64,
            ).grid(row=0, column=2, rowspan=2, padx=10)

    # ── Обработчики ───────────────────────────────────────────

    def _on_group_selected(self, group: str) -> None:
        self._selected = None
        self._set_generate_enabled(False)
        self._students = {}
        for student in self._sources.students.students(group):
            name = student.display_name
            suffix = 2
            while name in self._students:  # полные тёзки в одной группе
                name = f"{student.display_name} ({suffix})"
                suffix += 1
            self._students[name] = student

        if self._students:
            self._student_menu.configure(values=list(self._students), state="normal")
            self._student_menu.set(STUDENT_PLACEHOLDER)
            self._hint.configure(text="")
        else:
            self._student_menu.configure(values=[], state="disabled")
            self._student_menu.set(STUDENT_EMPTY)
            self._hint.configure(text=f"На листе «{group}» нет ни одного студента")

    def _on_student_selected(self, name: str) -> None:
        self._selected = self._students.get(name)
        self._set_generate_enabled(self._selected is not None)

    def _on_generate(self) -> None:
        if self._selected is None:
            return
        self._set_generate_enabled(False)
        self._generate_button.configure(text="Сохраняю…")
        self.update_idletasks()
        try:
            issued = self._issue_with_retry(self._selected)
        finally:
            self._generate_button.configure(text="Сгенерировать билет")
        if issued is None:
            self._set_generate_enabled(True)
            return
        self._refresh_journal_views()
        ResultWindow(self, issued, self._fonts, on_close=self._ready_for_next_student)

    def _issue_with_retry(self, student: Student):
        while True:
            try:
                return self._sources.service.issue(student)
            except JournalLockedError:
                retry = messagebox.askretrycancel(
                    "Журнал занят",
                    "Файл results.xlsx открыт в Excel, и закрыть его автоматически не удалось "
                    "(возможно, редактируется ячейка или открыт диалог).\n\n"
                    "Закройте файл в Excel и нажмите «Повторить».",
                    parent=self,
                )
                if not retry:
                    return None
            except JournalError as exc:
                messagebox.showerror("Ошибка журнала", f"{exc}.\n\nБилет не выдан.", parent=self)
                return None

    def _ready_for_next_student(self) -> None:
        """После закрытия результата группа остаётся выбранной, студент — сбрасывается."""
        self._selected = None
        if self._students:
            self._student_menu.set(STUDENT_PLACEHOLDER)
        self._set_generate_enabled(False)
        self.focus_force()

    def _set_generate_enabled(self, enabled: bool) -> None:
        self._generate_button.configure(
            state="normal" if enabled else "disabled",
            fg_color=theme.ACCENT if enabled else theme.DISABLED,
        )

    def _toggle_theme(self) -> None:
        ctk.set_appearance_mode("dark" if self._theme_switch.get() else "light")

    # ── Мелкие фабрики виджетов ───────────────────────────────

    def _field_label(self, master, text: str, top: int = 0) -> None:
        ctk.CTkLabel(master, text=text, font=self._fonts.label, text_color=theme.MUTED, anchor="w").pack(
            fill="x", pady=(top, 6)
        )

    def _option_menu(self, master, values: list[str], command) -> ctk.CTkOptionMenu:
        menu = ctk.CTkOptionMenu(
            master,
            values=values,
            command=command,
            height=44,
            corner_radius=10,
            dynamic_resizing=False,
            font=self._fonts.body,
            dropdown_font=self._fonts.body,
            fg_color=theme.FIELD,
            button_color=theme.FIELD,
            button_hover_color=theme.FIELD_HOVER,
            text_color=theme.TEXT,
            text_color_disabled=theme.MUTED,
            dropdown_fg_color=theme.CARD,
            dropdown_hover_color=theme.ACCENT_SOFT,
            dropdown_text_color=theme.TEXT,
        )
        menu.pack(fill="x")
        return menu

    def _primary_button(self, master, text: str, command) -> ctk.CTkButton:
        return ctk.CTkButton(
            master,
            text=text,
            height=44,
            corner_radius=12,
            font=self._fonts.button,
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.ON_ACCENT,
            text_color_disabled=theme.MUTED,
            command=command,
        )

    def _muted_line(self, master, text: str) -> None:
        ctk.CTkLabel(master, text=text, font=self._fonts.small, text_color=theme.MUTED).pack(anchor="w", padx=8, pady=6)
