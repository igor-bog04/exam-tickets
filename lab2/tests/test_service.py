import random
from datetime import datetime

import pytest

from ticket_ui.errors import JournalLockedError
from ticket_ui.models import Student, Ticket
from ticket_ui.results import ExcelResultsJournal
from ticket_ui.service import TicketService

IVANOV = Student("IS-231", "Иванов", "Иван")
PETROVA = Student("IS-231", "Петрова", "Анна")


class FakeCatalog:
    def __init__(self, numbers):
        self._tickets = {n: Ticket(n, (f"q{n}.1", f"q{n}.2", f"q{n}.3")) for n in numbers}

    def all(self):
        return list(self._tickets.values())

    def get(self, number):
        return self._tickets.get(number)


class FakeCloser:
    def __init__(self, journal=None):
        self.journal = journal
        self.calls = 0

    def close(self, path):
        self.calls += 1
        if self.journal is None:
            return False
        self.journal.locked = 0
        return True


class LockableJournal(ExcelResultsJournal):
    def __init__(self, path, locked=0):
        super().__init__(path)
        self.locked = locked

    def append(self, record):
        if self.locked:
            raise JournalLockedError("locked")
        super().append(record)


def make_service(journal, catalog=None, closer=None, seed=1):
    return TicketService(
        catalog or FakeCatalog(range(1, 21)),
        journal,
        closer or FakeCloser(),
        rng=random.Random(seed),
        clock=lambda: datetime(2026, 11, 4, 12, 0),
        sleep=lambda _: None,
    )


def test_new_student_gets_ticket_from_catalog_and_no_repeat(tmp_path):
    service = make_service(ExcelResultsJournal(tmp_path / "results.xlsx"), FakeCatalog([3, 8, 15]))

    issued = service.issue(IVANOV)

    assert issued.record.ticket_number in {3, 8, 15}
    assert issued.ticket.number == issued.record.ticket_number
    assert issued.record.repeat is False


def test_repeat_selection_returns_same_ticket_and_appends_new_row(tmp_path):
    journal = ExcelResultsJournal(tmp_path / "results.xlsx")
    first = make_service(journal, seed=1).issue(IVANOV)

    # другой seed: если бы билет выбирался случайно, номер почти наверняка отличался бы
    for seed in range(2, 7):
        again = make_service(journal, seed=seed).issue(IVANOV)
        assert again.record.ticket_number == first.record.ticket_number
        assert again.record.repeat is True

    records = journal.records()
    assert len(records) == 6
    assert [r.repeat for r in records] == [False] + [True] * 5


def test_students_are_independent(tmp_path):
    journal = ExcelResultsJournal(tmp_path / "results.xlsx")
    service = make_service(journal)
    service.issue(IVANOV)

    assert service.issue(PETROVA).record.repeat is False


def test_repeat_ticket_missing_from_catalog_still_issues_number(tmp_path):
    journal = ExcelResultsJournal(tmp_path / "results.xlsx")
    first = make_service(journal, FakeCatalog([5])).issue(IVANOV)

    again = make_service(journal, FakeCatalog([6])).issue(IVANOV)

    assert again.record.ticket_number == first.record.ticket_number == 5
    assert again.ticket is None


def test_locked_journal_is_closed_automatically(tmp_path):
    journal = LockableJournal(tmp_path / "results.xlsx", locked=1)
    closer = FakeCloser(journal)

    issued = make_service(journal, closer=closer).issue(IVANOV)

    assert closer.calls == 1
    assert journal.records()[0].ticket_number == issued.record.ticket_number


def test_locked_journal_raises_when_auto_close_fails(tmp_path):
    journal = LockableJournal(tmp_path / "results.xlsx", locked=1)

    with pytest.raises(JournalLockedError):
        make_service(journal).issue(IVANOV)
    assert journal.records() == []
