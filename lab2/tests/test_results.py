from datetime import datetime

import pytest
from openpyxl import load_workbook

from ticket_ui.errors import JournalLockedError
from ticket_ui.models import ResultRecord, Student
from ticket_ui.results import HEADER, ExcelResultsJournal

IVANOV = Student("IS-231", "Иванов", "Иван")


def record(student: Student, ticket: int, minute: int = 0, repeat: bool = False) -> ResultRecord:
    return ResultRecord(student, ticket, datetime(2026, 11, 4, 10, minute), repeat)


def rows(path):
    return [tuple(row) for row in load_workbook(path).active.iter_rows(values_only=True)]


def test_creates_journal_with_header(tmp_path):
    path = tmp_path / "results.xlsx"
    ExcelResultsJournal(path).append(record(IVANOV, 5))

    assert rows(path) == [HEADER, ("IS-231", "Иванов", "Иван", 5, datetime(2026, 11, 4, 10, 0), "нет")]


def test_appends_to_end_without_changing_existing_rows(tmp_path):
    path = tmp_path / "results.xlsx"
    ExcelResultsJournal(path).append(record(IVANOV, 5, minute=1))
    before = rows(path)

    ExcelResultsJournal(path).append(record(IVANOV, 5, minute=2, repeat=True))

    after = rows(path)
    assert after[:2] == before
    assert after[2][-1] == "да"


def test_first_ticket_of_uses_earliest_record_and_ignores_case(tmp_path):
    journal = ExcelResultsJournal(tmp_path / "results.xlsx")
    journal.append(record(IVANOV, 5, minute=1))
    journal.append(record(Student("IS-231", "Иванов", "Иван"), 9, minute=2))

    assert journal.first_ticket_of(Student("is-231", " ИВАНОВ ", "иван")) == 5
    assert journal.first_ticket_of(Student("IS-232", "Иванов", "Иван")) is None


def test_records_are_chronological(tmp_path):
    journal = ExcelResultsJournal(tmp_path / "results.xlsx")
    for minute in range(3):
        journal.append(record(IVANOV, 1, minute=minute))

    assert [r.issued_at.minute for r in journal.records()] == [0, 1, 2]


def test_missing_journal_has_no_records(tmp_path):
    assert ExcelResultsJournal(tmp_path / "results.xlsx").records() == []


def test_locked_journal_raises_and_keeps_rows(tmp_path):
    win32file = pytest.importorskip("win32file")
    path = tmp_path / "results.xlsx"
    ExcelResultsJournal(path).append(record(IVANOV, 1))

    handle = win32file.CreateFile(str(path), win32file.GENERIC_READ, win32file.FILE_SHARE_READ, None, win32file.OPEN_EXISTING, 0, None)
    try:
        with pytest.raises(JournalLockedError):
            ExcelResultsJournal(path).append(record(IVANOV, 2))
    finally:
        handle.Close()

    assert len(rows(path)) == 2
