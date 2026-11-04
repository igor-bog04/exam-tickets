"""Предметная модель: студенты, билеты, записи журнала."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Student:
    group: str
    last_name: str
    first_name: str

    @property
    def display_name(self) -> str:
        return f"{self.last_name} {self.first_name}"

    def matches(self, group: str, last_name: str, first_name: str) -> bool:
        """Сравнение без учёта регистра и пробелов по краям."""
        return (
            _norm(self.group) == _norm(group)
            and _norm(self.last_name) == _norm(last_name)
            and _norm(self.first_name) == _norm(first_name)
        )


@dataclass(frozen=True)
class Ticket:
    number: int
    questions: tuple[str, ...]


@dataclass(frozen=True)
class ResultRecord:
    student: Student
    ticket_number: int
    issued_at: datetime
    repeat: bool


@dataclass(frozen=True)
class IssuedTicket:
    record: ResultRecord
    ticket: Ticket | None  # None — номер есть в журнале, но билета больше нет в tickets.docx


def _norm(value: str) -> str:
    return " ".join(str(value).split()).casefold()
