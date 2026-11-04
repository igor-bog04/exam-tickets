import io
import random
from datetime import datetime
from pathlib import Path

from ticket_generator.app import TicketApp
from ticket_generator.console import Console
from ticket_generator.journal import JournalLockedError
from ticket_generator.tickets import TicketGenerator


class FakeKeys:
    def __init__(self, keys: str) -> None:
        self._keys = iter(keys)

    def read_key(self) -> str:
        return next(self._keys)


class FakeJournal:
    def __init__(self, locked_times: int = 0) -> None:
        self.path = Path("journal.xlsx")
        self.entries = []
        self._locked_times = locked_times

    def append(self, entry) -> None:
        if self._locked_times:
            self._locked_times -= 1
            raise JournalLockedError("locked")
        self.entries.append(entry)


class FakeCloser:
    def __init__(self, result: bool) -> None:
        self.result = result
        self.calls = 0

    def close(self, path) -> bool:
        self.calls += 1
        return self.result


def make_app(keys: str, journal: FakeJournal, closer: FakeCloser | None = None):
    out = io.StringIO()
    app = TicketApp(
        console=Console(FakeKeys(keys), out=out, colors=False),
        tickets=TicketGenerator(rng=random.Random(42)),
        journal=journal,
        closer=closer or FakeCloser(False),
        clock=lambda: datetime(2026, 11, 4, 9, 0),
        sleep=lambda _: None,
    )
    return app, out


def test_three_students_then_escape():
    journal = FakeJournal()
    app, out = make_app("A\rB\rC\rD\rE\rF\r\x1b", journal)
    app.run()

    assert [(e.last_name, e.first_name) for e in journal.entries] == [("A", "B"), ("C", "D"), ("E", "F")]
    assert all(1 <= e.ticket <= 20 for e in journal.entries)
    assert "Для выхода нажмите ESC." in out.getvalue()
    assert "Билет № " in out.getvalue()


def test_locked_journal_is_closed_automatically():
    journal = FakeJournal(locked_times=2)
    closer = FakeCloser(True)
    app, out = make_app("A\rB\r\x1b", journal, closer)
    app.run()

    assert closer.calls == 1
    assert len(journal.entries) == 1


def test_locked_journal_asks_user_when_auto_close_fails():
    journal = FakeJournal(locked_times=1)
    app, out = make_app("A\rB\r\r\x1b", journal, FakeCloser(False))
    app.run()

    assert len(journal.entries) == 1
    assert "Закройте файл в Excel" in out.getvalue()


def test_user_can_skip_record_when_file_stays_locked():
    journal = FakeJournal(locked_times=100)
    app, out = make_app("A\rB\r\x1b\x1b", journal, FakeCloser(False))
    app.run()

    assert journal.entries == []
    assert "Запись не сохранена." in out.getvalue()
