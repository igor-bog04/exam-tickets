"""Точка входа: собирает зависимости и запускает приложение."""

from pathlib import Path

from ticket_generator.app import TicketApp
from ticket_generator.console import Console, MsvcrtKeySource
from ticket_generator.excel_closer import ExcelWorkbookCloser
from ticket_generator.journal import ExcelJournal
from ticket_generator.tickets import TicketGenerator

JOURNAL_PATH = Path(__file__).resolve().parent / "journal.xlsx"


def main() -> None:
    app = TicketApp(
        console=Console(MsvcrtKeySource()),
        tickets=TicketGenerator(1, 20),
        journal=ExcelJournal(JOURNAL_PATH),
        closer=ExcelWorkbookCloser(),
    )
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nПрервано.")


if __name__ == "__main__":
    main()
