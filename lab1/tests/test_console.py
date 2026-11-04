import io

import pytest

from ticket_generator.console import Console, EscapePressed


class FakeKeys:
    def __init__(self, keys: str) -> None:
        self._keys = iter(keys)

    def read_key(self) -> str:
        return next(self._keys)


def console(keys: str) -> Console:
    return Console(FakeKeys(keys), out=io.StringIO(), colors=False)


def test_reads_line_until_enter():
    assert console("Ivanov\r").read_line("> ") == "Ivanov"


def test_backspace_removes_last_char():
    assert console("Ivx\x08anov\r").read_line("> ") == "Ivanov"


def test_escape_raises():
    with pytest.raises(EscapePressed):
        console("Iv\x1b").read_line("> ")


def test_escape_as_first_key_raises():
    with pytest.raises(EscapePressed):
        console("\x1b").ask_required("Last name: ")


def test_required_field_repeats_on_empty_and_trims_spaces():
    assert console("\r   \r  Petrov  \r").ask_required("Last name: ") == "Petrov"


def test_supports_cyrillic_and_ignores_special_keys():
    assert console("Иван\x00ов\r").read_line("> ") == "Иванов"


def test_confirm():
    assert console("\r").confirm("?") is True
    assert console("\x1b").confirm("?") is False
