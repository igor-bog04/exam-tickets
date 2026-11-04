"""Выбор номера экзаменационного билета."""

from __future__ import annotations

import random


class TicketGenerator:
    def __init__(self, first: int = 1, last: int = 20, rng: random.Random | None = None) -> None:
        if first > last:
            raise ValueError("Диапазон билетов пуст")
        self._first = first
        self._last = last
        self._rng = rng or random.Random()

    def next_ticket(self) -> int:
        return self._rng.randint(self._first, self._last)
