"""Точка входа: настраивает журналирование и открывает главное окно."""

import logging
from pathlib import Path

import customtkinter as ctk

from ticket_ui.bootstrap import load_sources
from ticket_ui.ui.main_window import MainWindow

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_FILE = BASE_DIR / "app.log"


def main() -> None:
    logging.basicConfig(
        filename=LOG_FILE,
        encoding="utf-8",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    ctk.set_appearance_mode("system")
    MainWindow(lambda: load_sources(DATA_DIR), log_name=LOG_FILE.name).mainloop()


if __name__ == "__main__":
    main()
