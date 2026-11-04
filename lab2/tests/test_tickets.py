import pytest
from docx import Document

from ticket_ui.errors import SourceError
from ticket_ui.tickets import DocxTicketCatalog, Paragraph, parse_tickets


def paragraphs(*lines: str) -> list[Paragraph]:
    return [Paragraph(line) for line in lines]


def test_parses_tickets_in_documented_format():
    result = parse_tickets(paragraphs(
        "Экзаменационные билеты",
        "Билет 1", "1. Первый", "2. Второй", "3. Третий", "",
        "Билет 2", "1. A", "2. B", "3. C",
    ))

    assert [(t.number, t.questions) for t in result.tickets] == [
        (1, ("Первый", "Второй", "Третий")),
        (2, ("A", "B", "C")),
    ]
    assert result.problems == []


def test_accepts_header_variants_and_word_auto_numbering():
    result = parse_tickets([
        Paragraph("БИЛЕТ № 7."),
        Paragraph("Вопрос без номера в тексте", numbered=True),
        Paragraph("2) Второй"),
        Paragraph("3.Третий"),
    ])

    assert result.tickets[0].number == 7
    assert result.tickets[0].questions == ("Вопрос без номера в тексте", "Второй", "Третий")


def test_ticket_with_less_than_three_questions_is_skipped_and_logged(caplog):
    result = parse_tickets(paragraphs(
        "Билет 1", "1. A", "2. B",
        "Билет 2", "1. A", "2. B", "3. C",
    ))

    assert [t.number for t in result.tickets] == [2]
    assert "Билет 1" in result.problems[0]
    assert "Билет 1" in caplog.text


def test_unrecognized_header_skips_its_questions():
    result = parse_tickets(paragraphs(
        "Билет X", "1. A", "2. B", "3. C",
        "Билет 2", "1. D", "2. E", "3. F",
    ))

    assert [(t.number, t.questions) for t in result.tickets] == [(2, ("D", "E", "F"))]
    assert "Билет X" in result.problems[0]


def test_duplicate_number_and_extra_questions():
    result = parse_tickets(paragraphs(
        "Билет 1", "1. A", "2. B", "3. C", "4. D",
        "Билет 1", "1. E", "2. F", "3. G",
    ))

    assert [(t.number, t.questions) for t in result.tickets] == [(1, ("A", "B", "C"))]
    assert len(result.problems) == 2


def test_reads_real_docx_with_auto_numbered_questions(tmp_path):
    path = tmp_path / "tickets.docx"
    document = Document()
    document.add_paragraph("Билет 1")
    for text in ("Первый", "Второй", "Третий"):
        document.add_paragraph(text, style="List Number")
    document.add_paragraph("Билет 2")
    for index, text in enumerate(("A", "B", "C"), start=1):
        document.add_paragraph(f"{index}. {text}")
    document.save(path)

    catalog = DocxTicketCatalog(path)

    assert [t.number for t in catalog.all()] == [1, 2]
    assert catalog.get(1).questions == ("Первый", "Второй", "Третий")
    assert catalog.get(99) is None


def test_missing_docx_raises_source_error(tmp_path):
    with pytest.raises(SourceError, match="tickets.docx"):
        DocxTicketCatalog(tmp_path / "tickets.docx")


def test_corrupted_docx_raises_source_error(tmp_path):
    path = tmp_path / "tickets.docx"
    path.write_text("not a docx")

    with pytest.raises(SourceError):
        DocxTicketCatalog(path)


def test_docx_without_valid_tickets_raises_source_error(tmp_path):
    path = tmp_path / "tickets.docx"
    document = Document()
    document.add_paragraph("Билет 1")
    document.add_paragraph("1. Только один вопрос")
    document.save(path)

    with pytest.raises(SourceError, match="нет ни одного"):
        DocxTicketCatalog(path)
