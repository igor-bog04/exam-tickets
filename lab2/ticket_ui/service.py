"""Выдача билета: повторный студент получает билет из своей первой записи."""

from __future__ import annotations

import random
import time
from datetime import datetime
from typing import Callable

from .errors import JournalLockedError
from .excel_closer import WorkbookCloser
from .models import IssuedTicket, ResultRecord, Student
from .results import ResultsJournal
from .tickets import TicketCatalog

RELEASE_ATTEMPTS = 10
RELEASE_DELAY_SECONDS = 0.3


class TicketService:
    def __init__(
        self,
        catalog: TicketCatalog,
        journal: ResultsJournal,
        closer: WorkbookCloser,
        rng: random.Random | None = None,
        clock: Callable[[], datetime] = datetime.now,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._catalog = catalog
        self._journal = journal
        self._closer = closer
        self._rng = rng or random.Random()
        self._clock = clock
        self._sleep = sleep

    def issue(self, student: Student) -> IssuedTicket:
        """Назначает билет и сразу сохраняет запись.

        Если журнал открыт в Excel, книга закрывается автоматически.
        Если это не удалось — JournalLockedError, и ничего не записано.
        """
        try:
            return self._issue(student)
        except JournalLockedError:
            if not self._closer.close(self._journal.path):
                raise
        # После закрытия книги Excel отпускает файл не мгновенно.
        for _ in range(RELEASE_ATTEMPTS - 1):
            try:
                return self._issue(student)
            except JournalLockedError:
                self._sleep(RELEASE_DELAY_SECONDS)
        return self._issue(student)

    def _issue(self, student: Student) -> IssuedTicket:
        first_ticket = self._journal.first_ticket_of(student)
        if first_ticket is None:
            ticket = self._rng.choice(self._catalog.all())
            number, repeat = ticket.number, False
        else:
            number, repeat = first_ticket, True
        record = ResultRecord(student, number, self._clock().replace(microsecond=0), repeat)
        self._journal.append(record)
        return IssuedTicket(record, self._catalog.get(number))
