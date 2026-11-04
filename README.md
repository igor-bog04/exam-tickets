# Exam Ticket Generator

Laboratory works on building small, reliable tools that assign exam tickets to students and keep a journal of every assignment in Excel.

| Lab | Description | Status |
|-----|-------------|--------|
| [Lab 1](lab1/) | Console ticket generator with an Excel journal | Done |
| [Lab 2](lab2/) | Desktop GUI generator: students from Excel, questions from Word | Done |

## Requirements

- Windows 10/11
- Python 3.11+
- Microsoft Excel (optional; only needed to view the journal)

## Setup

```bash
git clone <repository-url>
cd exam-tickets
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Lab 1 — Console ticket generator

### Run

```bash
cd lab1
python main.py
```

```
══════ Генератор экзаменационных билетов ══════
Для выхода нажмите ESC.

Last name: Ivanov
First name: Ivan
Билет № 7
  Запись добавлена в journal.xlsx
```

Press **ESC** at any prompt to quit.

### Features

- Ticket number is drawn uniformly from 1 to 20.
- Every student is written to `lab1/journal.xlsx` (`Last name | First name | Номер билета | Дата и время`). The file is created with a styled header on first run; later runs only append rows.
- **Crash-safe saving.** The journal is saved right after each student. Each save writes a temporary file and atomically replaces the journal, so killing the process mid-save never corrupts earlier records.
- **Input validation.** Empty input is rejected and the prompt is repeated; leading and trailing spaces are trimmed. Cyrillic input is supported.
- **Journal open in Excel.** If `journal.xlsx` is open in Excel, the app finds that workbook in the running Excel instance, saves the user's edits, closes only that workbook and appends the record. If the workbook cannot be closed automatically (for example, a cell is being edited), the app asks the user to close it and retry — it never crashes.

### Architecture

The code follows SOLID principles: each module has a single responsibility, and the application depends on small protocols rather than concrete classes, so every dependency can be replaced with a fake in tests.

```
lab1/
├── main.py                     # Composition root: wires concrete implementations together
└── ticket_generator/
    ├── app.py                  # TicketApp — workflow: read student → draw ticket → save
    ├── console.py              # Console — key-by-key line input with ESC/Backspace, colored output
    ├── tickets.py              # TicketGenerator — random ticket in a configurable range
    ├── journal.py              # ExcelJournal — append-only, atomic Excel storage
    └── excel_closer.py         # ExcelWorkbookCloser — closes the journal in Excel via COM
```

| Principle | How it is applied |
|-----------|-------------------|
| Single responsibility | Input, ticket drawing, storage and Excel automation live in separate classes. |
| Open/closed | A new storage (CSV, database) is added by implementing `Journal`, without touching `TicketApp`. |
| Liskov substitution | Test fakes and real implementations are interchangeable behind the same protocols. |
| Interface segregation | Protocols are minimal: `Journal.append`, `WorkbookCloser.close`, `KeySource.read_key`. |
| Dependency inversion | `TicketApp` receives all dependencies through its constructor; only `main.py` knows concrete types. |

### Tests

```bash
cd lab1
python -m pytest
```

The tests cover journal creation and appending, protection of existing rows, locked and corrupted files, keyboard input (ESC, Backspace, empty input, trimming) and the full application workflow, including automatic closing of a locked journal.

### Manual acceptance checklist

1. Enter three students, press ESC — the journal has a header and three rows.
2. Run again and enter two students — five rows, the first three unchanged.
3. Kill the app in Task Manager after entering a student — the record is in the file.
4. Open `journal.xlsx` in Excel and enter a student — the workbook is closed automatically and the record is saved.
5. Press Enter on an empty field — the prompt is repeated.

## Lab 2 — Desktop ticket generator

A desktop app built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter): pick a group and a student, get a ticket with three questions.

### Run

```bash
cd lab2
python main.py
```

Input files live in `lab2/data/`:

| File | Format |
|------|--------|
| `students.xlsx` | One sheet per group (sheet name = group). Row 1 is a header; column A — last name, column B — first name. |
| `tickets.docx` | A paragraph `Билет N`, followed by numbered questions `1. text`. Word auto-numbered lists are supported too. |

Demo files are included. Regenerate them with `python tools/make_sample_data.py`.

### Features

- **Group → student selection.** The second list is filled with the students of the selected sheet in the format `Last First`. The **Generate** button is enabled only when both are selected.
- **Result window.** Shows `Ваш билет № N` and the three questions. **Esc** closes only this window and returns to the selection, ready for the next student.
- **Ticket assignment.** A new student gets a random ticket from those parsed from `tickets.docx`. A student who already has a record (group + last name + first name, case-insensitive) gets the ticket from their **first** record again; a new row is appended with `Повтор = да`.
- **Results journal.** `lab2/data/results.xlsx` (`Группа | Фамилия | Имя | Номер билета | Дата и время | Повтор`) is created on first use and saved atomically right after each generation. Existing rows are never modified, so the journal is a complete chronological history.
- **Journal open in Excel.** The workbook is closed automatically in Excel (user edits are saved) and the record is written. If that fails, the user gets a *Retry / Cancel* dialog — the app never crashes.
- **Robust parsing.** A ticket with fewer than three questions, an unrecognized header or a duplicate number is skipped and logged to `lab2/app.log`; the app keeps working with the remaining tickets and shows a warning banner.
- **Missing sources.** If `students.xlsx` or `tickets.docx` is missing or broken, the window shows a clear message with a *Retry* button.
- **Empty group.** A group sheet without students leaves the student list empty and the button disabled.
- **Light and dark themes**, a dashboard with statistics, and a list of the latest assignments.

### Architecture

```
lab2/
├── main.py                     # Entry point: logging setup, main window
├── data/                       # students.xlsx, tickets.docx, results.xlsx (generated)
├── tools/make_sample_data.py   # Generates demo input files
└── ticket_ui/
    ├── models.py               # Student, Ticket, ResultRecord, IssuedTicket
    ├── students.py             # ExcelStudentRepository — groups and students from Excel
    ├── tickets.py              # parse_tickets() + DocxTicketCatalog — tickets from Word
    ├── results.py              # ExcelResultsJournal — append-only results journal
    ├── service.py              # TicketService — ticket assignment and repeat rule
    ├── excel_closer.py         # ExcelWorkbookCloser — closes the journal in Excel via COM
    ├── bootstrap.py            # Composition root: builds services from the data folder
    └── ui/
        ├── theme.py            # Color palette (light/dark), fonts, layout helpers
        ├── main_window.py      # Group/student selection, stats, recent assignments
        └── result_window.py    # Ticket and questions, closed by Esc
```

SOLID in practice:

- **Single responsibility** — reading students, parsing tickets, writing the journal, assigning tickets and rendering the UI are separate modules.
- **Open/closed** — the parser works on plain `Paragraph` objects, so another source (PDF, database) only needs a new reader.
- **Liskov substitution** — tests replace the catalog, journal and Excel closer with fakes that honor the same contracts.
- **Interface segregation** — `StudentRepository`, `TicketCatalog`, `ResultsJournal` and `WorkbookCloser` are small protocols.
- **Dependency inversion** — `TicketService` and `MainWindow` depend on protocols; concrete classes are wired only in `bootstrap.py`.

### Tests

```bash
cd lab2
python -m pytest
```

Covered: ticket parsing from Word (format variants, auto-numbering, broken tickets, missing or corrupt files), student lookup by group (including empty groups), the append-only journal, repeat selection returning the same ticket (idempotency), and automatic handling of a locked journal.
