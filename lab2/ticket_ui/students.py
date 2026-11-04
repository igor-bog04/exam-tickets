"""Список студентов из students.xlsx: один лист — одна группа."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Protocol

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from .errors import SourceError
from .models import Student


class StudentRepository(Protocol):
    def groups(self) -> list[str]: ...

    def students(self, group: str) -> list[Student]: ...


class ExcelStudentRepository:
    """Читает книгу один раз при создании. Строка 1 — заголовок, A — фамилия, B — имя."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._by_group = self._load()

    def groups(self) -> list[str]:
        return list(self._by_group)

    def students(self, group: str) -> list[Student]:
        return list(self._by_group.get(group, ()))

    def _load(self) -> dict[str, list[Student]]:
        if not self.path.exists():
            raise SourceError(f"Не найден файл со студентами: {self.path.name}")
        try:
            workbook = load_workbook(self.path, read_only=True, data_only=True)
        except (InvalidFileException, zipfile.BadZipFile, KeyError, OSError) as exc:
            raise SourceError(f"Не удалось прочитать {self.path.name}: файл повреждён или занят") from exc

        try:
            result: dict[str, list[Student]] = {}
            for sheet in workbook.worksheets:
                students = []
                for row in sheet.iter_rows(min_row=2, max_col=2, values_only=True):
                    last, first = (_cell(value) for value in (tuple(row) + (None, None))[:2])
                    if last and first:
                        students.append(Student(sheet.title, last, first))
                result[sheet.title] = students
            return result
        finally:
            workbook.close()


def _cell(value) -> str:
    return "" if value is None else " ".join(str(value).split())
