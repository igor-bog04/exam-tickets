"""Сценарий работы приложения: ввод студента → билет → запись в журнал."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

from .console import Console, EscapePressed, Style
from .excel_closer import WorkbookCloser
from .journal import Journal, JournalEntry, JournalError, JournalLockedError
from .tickets import TicketGenerator

RELEASE_ATTEMPTS = 10
RELEASE_DELAY_SECONDS = 0.3


class TicketApp:
    def __init__(
        self,
        console: Console,
        tickets: TicketGenerator,
        journal: Journal,
        closer: WorkbookCloser,
        clock: Callable[[], datetime] = datetime.now,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._console = console
        self._tickets = tickets
        self._journal = journal
        self._closer = closer
        self._clock = clock
        self._sleep = sleep

    def run(self) -> None:
        self._console.print("══════ Генератор экзаменационных билетов ══════", Style.BOLD, Style.CYAN)
        self._console.print("Для выхода нажмите ESC.", Style.DIM)
        try:
            while True:
                self._serve_student()
        except EscapePressed:
            self._console.print("Работа завершена. Журнал сохранён.", Style.CYAN)

    def _serve_student(self) -> None:
        self._console.print()
        last_name = self._console.ask_required("Last name: ")
        first_name = self._console.ask_required("First name: ")
        ticket = self._tickets.next_ticket()
        self._console.print(f"Билет № {ticket}", Style.BOLD, Style.GREEN)
        entry = JournalEntry(last_name, first_name, ticket, self._clock().replace(microsecond=0))
        if self._save(entry):
            self._console.print(f"  Запись добавлена в {self._journal.path.name}", Style.DIM)

    def _save(self, entry: JournalEntry) -> bool:
        auto_close_tried = False
        while True:
            try:
                self._journal.append(entry)
                return True
            except JournalLockedError:
                if not auto_close_tried:
                    auto_close_tried = True
                    self._console.print(
                        f"  {self._journal.path.name} открыт в Excel — закрываю его (ваши правки сохранятся)...",
                        Style.YELLOW,
                    )
                    if self._closer.close(self._journal.path) and self._append_after_release(entry):
                        return True
                message = f"  Не удалось закрыть {self._journal.path.name}. Закройте файл в Excel."
            except JournalError as exc:
                message = f"  Ошибка записи: {exc}."
            except OSError as exc:
                message = f"  Ошибка записи: {exc.strerror or exc}."

            self._console.print(message, Style.RED)
            if not self._console.confirm("  Enter — повторить, ESC — пропустить запись: "):
                self._console.print("  Запись не сохранена.", Style.RED)
                return False

    def _append_after_release(self, entry: JournalEntry) -> bool:
        """После закрытия книги Excel отпускает файл не мгновенно — даём ему немного времени."""
        for _ in range(RELEASE_ATTEMPTS):
            try:
                self._journal.append(entry)
                return True
            except JournalLockedError:
                self._sleep(RELEASE_DELAY_SECONDS)
        return False
