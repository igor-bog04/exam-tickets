"""Ошибки, которые интерфейс показывает пользователю понятным сообщением."""


class SourceError(Exception):
    """Входной файл (students.xlsx, tickets.docx) отсутствует или не читается."""


class JournalError(Exception):
    """Запись в results.xlsx не удалась."""


class JournalLockedError(JournalError):
    """results.xlsx занят другим приложением (обычно открыт в Excel)."""
