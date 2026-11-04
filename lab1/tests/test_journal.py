from datetime import datetime

import pytest
from openpyxl import load_workbook

from ticket_generator.journal import HEADER, ExcelJournal, JournalCorruptedError, JournalEntry, JournalLockedError


def entry(last: str, first: str = "Ivan", ticket: int = 1) -> JournalEntry:
    return JournalEntry(last, first, ticket, datetime(2026, 11, 4, 10, 30))


def rows(path):
    return [tuple(row) for row in load_workbook(path).active.iter_rows(values_only=True)]


def test_creates_file_with_header(tmp_path):
    path = tmp_path / "journal.xlsx"
    ExcelJournal(path).append(entry("Petrov", ticket=7))

    assert rows(path) == [HEADER, ("Petrov", "Ivan", 7, datetime(2026, 11, 4, 10, 30))]


def test_appends_without_touching_existing_rows(tmp_path):
    path = tmp_path / "journal.xlsx"
    for name in ("A", "B", "C"):
        ExcelJournal(path).append(entry(name))
    before = rows(path)

    journal = ExcelJournal(path)  # имитирует повторный запуск приложения
    journal.append(entry("D"))
    journal.append(entry("E"))

    after = rows(path)
    assert after[:4] == before
    assert [row[0] for row in after[1:]] == ["A", "B", "C", "D", "E"]


def test_locked_file_raises_locked_error(tmp_path):
    win32file = pytest.importorskip("win32file")
    path = tmp_path / "journal.xlsx"
    ExcelJournal(path).append(entry("A"))

    # Excel держит файл открытым без права записи для других процессов — делаем так же
    handle = win32file.CreateFile(
        str(path), win32file.GENERIC_READ, 0, None, win32file.OPEN_EXISTING, 0, None
    )
    try:
        with pytest.raises(JournalLockedError):
            ExcelJournal(path).append(entry("B"))
    finally:
        handle.Close()

    assert len(rows(path)) == 2


def test_corrupted_file_raises_corrupted_error(tmp_path):
    path = tmp_path / "journal.xlsx"
    path.write_text("not an excel file")

    with pytest.raises(JournalCorruptedError):
        ExcelJournal(path).append(entry("A"))


def test_no_temp_files_left_behind(tmp_path):
    path = tmp_path / "journal.xlsx"
    ExcelJournal(path).append(entry("A"))

    assert [p.name for p in tmp_path.iterdir()] == ["journal.xlsx"]
