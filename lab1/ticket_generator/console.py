"""Ввод с клавиатуры с поддержкой ESC и цветной вывод в консоль."""

from __future__ import annotations

import os
import sys
from typing import Protocol, TextIO

ESC = "\x1b"
ENTER = ("\r", "\n")
BACKSPACE = "\x08"
CTRL_C = "\x03"
SPECIAL_KEY_PREFIXES = ("\x00", "\xe0")


class EscapePressed(Exception):
    """Пользователь нажал ESC во время ожидания ввода."""


class KeySource(Protocol):
    def read_key(self) -> str:
        """Возвращает один символ; пустая строка — служебная клавиша (стрелки, F1...)."""
        ...


class MsvcrtKeySource:
    """Чтение клавиш из консоли Windows без ожидания Enter."""

    def read_key(self) -> str:
        import msvcrt

        key = msvcrt.getwch()
        if key in SPECIAL_KEY_PREFIXES:
            msvcrt.getwch()
            return ""
        return key


class Style:
    RESET = "\x1b[0m"
    BOLD = "\x1b[1m"
    DIM = "\x1b[2m"
    GREEN = "\x1b[92m"
    YELLOW = "\x1b[93m"
    RED = "\x1b[91m"
    CYAN = "\x1b[96m"


class Console:
    """Посимвольный ввод строки: Enter, Backspace и ESC обрабатываются вручную."""

    def __init__(self, keys: KeySource, out: TextIO = sys.stdout, colors: bool = True) -> None:
        self._keys = keys
        self._out = out
        self._colors = colors
        if colors and os.name == "nt":
            os.system("")  # включает ANSI-цвета в классической консоли Windows

    def print(self, text: str = "", *styles: str) -> None:
        if self._colors and styles:
            text = "".join(styles) + text + Style.RESET
        self._out.write(text + "\n")
        self._out.flush()

    def read_line(self, prompt: str) -> str:
        self._write(prompt)
        buffer: list[str] = []
        while True:
            key = self._keys.read_key()
            if key == ESC:
                self._write("\n")
                raise EscapePressed
            if key == CTRL_C:
                raise KeyboardInterrupt
            if key in ENTER:
                self._write("\n")
                return "".join(buffer)
            if key == BACKSPACE:
                if buffer:
                    buffer.pop()
                    self._write("\b \b")
                continue
            if key and key.isprintable():
                buffer.append(key)
                self._write(key)

    def ask_required(self, prompt: str) -> str:
        """Повторяет запрос, пока не будет введена непустая строка; пробелы по краям обрезаются."""
        while True:
            value = self.read_line(prompt).strip()
            if value:
                return value
            self.print("  Поле не может быть пустым, попробуйте ещё раз.", Style.YELLOW)

    def confirm(self, prompt: str) -> bool:
        """Enter — да, ESC — нет."""
        self._write(prompt)
        while True:
            key = self._keys.read_key()
            if key in ENTER:
                self._write("\n")
                return True
            if key == ESC:
                self._write("\n")
                return False
            if key == CTRL_C:
                raise KeyboardInterrupt

    def _write(self, text: str) -> None:
        self._out.write(text)
        self._out.flush()
