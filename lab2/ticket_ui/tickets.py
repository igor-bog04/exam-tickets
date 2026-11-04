"""Список билетов из tickets.docx.

Формат: абзац «Билет N», затем вопросы — абзацы «1. текст». Вопросы могут быть
оформлены и автонумерацией Word: тогда номера нет в тексте абзаца, и такой абзац
тоже считается вопросом.
"""

from __future__ import annotations

import logging
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Protocol

from .errors import SourceError
from .models import Ticket

log = logging.getLogger(__name__)

QUESTIONS_PER_TICKET = 3
TICKET_HEADER = re.compile(r"^билет\s*№?\s*(\d+)\s*\.?$", re.IGNORECASE)
TICKET_LIKE = re.compile(r"^билет\b", re.IGNORECASE)
QUESTION = re.compile(r"^(\d+)\s*[.)]\s*(.+)$")


@dataclass(frozen=True)
class Paragraph:
    text: str
    numbered: bool = False  # абзац оформлен автонумерацией Word


@dataclass
class ParseResult:
    tickets: list[Ticket] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


class TicketCatalog(Protocol):
    def all(self) -> list[Ticket]: ...

    def get(self, number: int) -> Ticket | None: ...


def parse_tickets(paragraphs: Iterable[Paragraph]) -> ParseResult:
    result = ParseResult()
    seen: set[int] = set()
    number: int | None = None
    questions: list[str] = []
    skipping = False  # внутри блока с нераспознанным заголовком

    def finish() -> None:
        if number is None:
            return
        if len(questions) < QUESTIONS_PER_TICKET:
            _problem(result, f"Билет {number}: найдено вопросов {len(questions)}, нужно {QUESTIONS_PER_TICKET} — пропущен")
        elif number in seen:
            _problem(result, f"Билет {number}: номер повторяется — пропущен")
        else:
            if len(questions) > QUESTIONS_PER_TICKET:
                _problem(result, f"Билет {number}: вопросов {len(questions)}, используются первые {QUESTIONS_PER_TICKET}")
            seen.add(number)
            result.tickets.append(Ticket(number, tuple(questions[:QUESTIONS_PER_TICKET])))

    for paragraph in paragraphs:
        text = " ".join(paragraph.text.split())
        if not text:
            continue

        header = TICKET_HEADER.match(text)
        if header:
            finish()
            number, questions, skipping = int(header.group(1)), [], False
            continue
        if TICKET_LIKE.match(text):
            finish()
            number, questions, skipping = None, [], True
            _problem(result, f"Заголовок не распознан: «{text}» — билет пропущен")
            continue

        question = QUESTION.match(text)
        question_text = question.group(2).strip() if question else (text if paragraph.numbered else None)
        if question_text is None or skipping:
            continue
        if number is None:
            _problem(result, f"Вопрос вне билета: «{text}» — пропущен")
            continue
        questions.append(question_text)

    finish()
    result.tickets.sort(key=lambda ticket: ticket.number)
    return result


def read_docx_paragraphs(path: Path) -> list[Paragraph]:
    from docx import Document
    from docx.opc.exceptions import PackageNotFoundError

    if not path.exists():
        raise SourceError(f"Не найден файл с билетами: {path.name}")
    try:
        document = Document(str(path))
    except (PackageNotFoundError, zipfile.BadZipFile, KeyError, OSError, ValueError) as exc:
        raise SourceError(f"Не удалось прочитать {path.name}: файл повреждён или занят") from exc
    return [Paragraph(p.text, _is_numbered(p)) for p in document.paragraphs]


def _is_numbered(paragraph) -> bool:
    properties = paragraph._p.pPr
    if properties is not None and properties.numPr is not None:
        return True
    style = paragraph.style.name if paragraph.style is not None else ""
    return style.startswith("List Number")


class DocxTicketCatalog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        parsed = parse_tickets(read_docx_paragraphs(self.path))
        self.problems = parsed.problems
        self._tickets = {ticket.number: ticket for ticket in parsed.tickets}
        if not self._tickets:
            raise SourceError(f"В {self.path.name} нет ни одного корректного билета")

    def all(self) -> list[Ticket]:
        return list(self._tickets.values())

    def get(self, number: int) -> Ticket | None:
        return self._tickets.get(number)


def _problem(result: ParseResult, message: str) -> None:
    log.warning(message)
    result.problems.append(message)
