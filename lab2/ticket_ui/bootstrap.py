"""Сборка зависимостей приложения из файлов в папке данных."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .excel_closer import ExcelWorkbookCloser
from .results import ExcelResultsJournal, ResultsJournal
from .service import TicketService
from .students import ExcelStudentRepository, StudentRepository
from .tickets import DocxTicketCatalog

STUDENTS_FILE = "students.xlsx"
TICKETS_FILE = "tickets.docx"
RESULTS_FILE = "results.xlsx"


@dataclass(frozen=True)
class Sources:
    students: StudentRepository
    catalog: DocxTicketCatalog
    journal: ResultsJournal
    service: TicketService


def load_sources(data_dir: Path) -> Sources:
    """Бросает SourceError, если входные файлы отсутствуют или не читаются."""
    students = ExcelStudentRepository(data_dir / STUDENTS_FILE)
    catalog = DocxTicketCatalog(data_dir / TICKETS_FILE)
    journal = ExcelResultsJournal(data_dir / RESULTS_FILE)
    service = TicketService(catalog, journal, ExcelWorkbookCloser())
    return Sources(students, catalog, journal, service)
