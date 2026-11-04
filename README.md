# Exam Ticket Generator

Laboratory works on building small, reliable tools that assign exam tickets to students and keep a journal of every assignment in Excel.

| Lab | Description | Status |
|-----|-------------|--------|
| [Lab 1](lab1/) | Console ticket generator with an Excel journal | Done |
| Lab 2 | Desktop GUI generator (students from Excel, questions from Word) | Planned (`lab2-ui-tickets` branch) |

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
