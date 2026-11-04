"""Журнал выданных билетов в Excel-файле."""

from __future__ import annotations

import os
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils.exceptions import InvalidFileException

HEADER = ("Last name", "First name", "Номер билета", "Дата и время")
COLUMN_WIDTHS = (22, 22, 16, 22)
DATE_FORMAT = "dd.mm.yyyy hh:mm:ss"


@dataclass(frozen=True)
class JournalEntry:
    last_name: str
    first_name: str
    ticket: int
    issued_at: datetime


class JournalError(Exception):
    """Запись в журнал не удалась."""


class JournalLockedError(JournalError):
    """Файл журнала занят другим приложением (обычно открыт в Excel)."""


class JournalCorruptedError(JournalError):
    """Файл журнала существует, но не читается как книга Excel."""


class Journal(Protocol):
    path: Path

    def append(self, entry: JournalEntry) -> None: ...


class ExcelJournal:
    """Дописывает строки в конец книги и сохраняет файл сразу после каждой записи.

    Сохранение атомарное: книга пишется во временный файл, который затем
    подменяет журнал. Если процесс убьют посреди сохранения, старый журнал
    останется целым.
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def append(self, entry: JournalEntry) -> None:
        self._ensure_writable()
        workbook = self._open_or_create()
        sheet = workbook.active
        sheet.append([entry.last_name, entry.first_name, entry.ticket, entry.issued_at])
        row = sheet.max_row
        sheet.cell(row=row, column=3).alignment = Alignment(horizontal="center")
        sheet.cell(row=row, column=4).number_format = DATE_FORMAT
        self._save_atomically(workbook)

    def _ensure_writable(self) -> None:
        if not self.path.exists():
            return
        try:
            with open(self.path, "r+b"):
                pass
        except PermissionError as exc:
            raise JournalLockedError(f"Файл {self.path.name} занят другим приложением") from exc

    def _open_or_create(self) -> Workbook:
        if not self.path.exists():
            return self._create_workbook()
        try:
            return load_workbook(self.path)
        except (InvalidFileException, zipfile.BadZipFile, KeyError) as exc:
            raise JournalCorruptedError(f"Файл {self.path.name} повреждён и не читается") from exc

    @staticmethod
    def _create_workbook() -> Workbook:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Journal"
        sheet.append(HEADER)
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor="305496")
        for column, width in enumerate(COLUMN_WIDTHS, start=1):
            cell = sheet.cell(row=1, column=column)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
            sheet.column_dimensions[cell.column_letter].width = width
        sheet.freeze_panes = "A2"
        return workbook

    def _save_atomically(self, workbook: Workbook) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=self.path.parent, prefix=".journal-", suffix=".tmp")
        os.close(fd)
        try:
            workbook.save(tmp_name)
            with open(tmp_name, "rb+") as tmp:
                os.fsync(tmp.fileno())
            os.replace(tmp_name, self.path)
        except PermissionError as exc:
            raise JournalLockedError(f"Файл {self.path.name} занят другим приложением") from exc
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
