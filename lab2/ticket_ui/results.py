"""Журнал результатов results.xlsx: только дописывание в конец."""

from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path
from typing import Protocol

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils.exceptions import InvalidFileException

from .errors import JournalError, JournalLockedError
from .models import ResultRecord, Student

HEADER = ("Группа", "Фамилия", "Имя", "Номер билета", "Дата и время", "Повтор (да/нет)")
COLUMN_WIDTHS = (14, 22, 18, 16, 22, 17)
DATE_FORMAT = "dd.mm.yyyy hh:mm:ss"
YES, NO = "да", "нет"


class ResultsJournal(Protocol):
    path: Path

    def first_ticket_of(self, student: Student) -> int | None: ...

    def append(self, record: ResultRecord) -> None: ...

    def records(self) -> list[ResultRecord]: ...


class ExcelResultsJournal:
    """Сохраняет файл сразу после каждой записи, атомарно через временный файл."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def first_ticket_of(self, student: Student) -> int | None:
        for record in self.records():
            if student.matches(record.student.group, record.student.last_name, record.student.first_name):
                return record.ticket_number
        return None

    def append(self, record: ResultRecord) -> None:
        self._ensure_writable()
        workbook = self._open() if self.path.exists() else self._create()
        sheet = workbook.active
        student = record.student
        sheet.append([
            student.group,
            student.last_name,
            student.first_name,
            record.ticket_number,
            record.issued_at,
            YES if record.repeat else NO,
        ])
        row = sheet.max_row
        for column in (4, 6):
            sheet.cell(row=row, column=column).alignment = Alignment(horizontal="center")
        sheet.cell(row=row, column=5).number_format = DATE_FORMAT
        self._save_atomically(workbook)

    def records(self) -> list[ResultRecord]:
        """Все записи журнала в хронологическом порядке."""
        if not self.path.exists():
            return []
        workbook = self._open(read_only=True)
        try:
            records = []
            for row in workbook.active.iter_rows(min_row=2, max_col=6, values_only=True):
                group, last, first, number, issued_at, repeat = (tuple(row) + (None,) * 6)[:6]
                try:
                    ticket_number = int(number)
                except (TypeError, ValueError):
                    continue
                if not (group and last and first):
                    continue
                student = Student(str(group), str(last), str(first))
                records.append(ResultRecord(student, ticket_number, issued_at, str(repeat).strip().lower() == YES))
            return records
        finally:
            workbook.close()

    def _ensure_writable(self) -> None:
        if not self.path.exists():
            return
        try:
            with open(self.path, "r+b"):
                pass
        except PermissionError as exc:
            raise JournalLockedError(f"{self.path.name} открыт в другой программе") from exc

    def _open(self, read_only: bool = False) -> Workbook:
        try:
            return load_workbook(self.path, read_only=read_only)
        except PermissionError as exc:
            raise JournalLockedError(f"{self.path.name} открыт в другой программе") from exc
        except (InvalidFileException, zipfile.BadZipFile, KeyError) as exc:
            raise JournalError(f"{self.path.name} повреждён и не читается") from exc

    @staticmethod
    def _create() -> Workbook:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Results"
        sheet.append(HEADER)
        for column, width in enumerate(COLUMN_WIDTHS, start=1):
            cell = sheet.cell(row=1, column=column)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="305496")
            cell.alignment = Alignment(horizontal="center")
            sheet.column_dimensions[cell.column_letter].width = width
        sheet.freeze_panes = "A2"
        return workbook

    def _save_atomically(self, workbook: Workbook) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=self.path.parent, prefix=".results-", suffix=".tmp")
        os.close(fd)
        try:
            workbook.save(tmp_name)
            with open(tmp_name, "rb+") as tmp:
                os.fsync(tmp.fileno())
            os.replace(tmp_name, self.path)
        except PermissionError as exc:
            raise JournalLockedError(f"{self.path.name} открыт в другой программе") from exc
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
