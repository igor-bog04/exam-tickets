import pytest
from openpyxl import Workbook

from ticket_ui.errors import SourceError
from ticket_ui.models import Student
from ticket_ui.students import ExcelStudentRepository


@pytest.fixture
def students_file(tmp_path):
    path = tmp_path / "students.xlsx"
    workbook = Workbook()
    workbook.remove(workbook.active)
    first = workbook.create_sheet("IS-231")
    first.append(("Фамилия", "Имя"))
    first.append(("Иванов", "Иван"))
    first.append(("  Петрова ", " Анна  "))
    first.append((None, None))  # пустая строка посреди листа
    first.append(("Без имени", None))
    second = workbook.create_sheet("IS-232")
    second.append(("Фамилия", "Имя"))
    second.append(("Сидоров", "Пётр"))
    empty = workbook.create_sheet("TI-251")
    empty.append(("Фамилия", "Имя"))
    workbook.save(path)
    return path


def test_groups_are_sheet_names_in_order(students_file):
    assert ExcelStudentRepository(students_file).groups() == ["IS-231", "IS-232", "TI-251"]


def test_students_of_group_match_its_sheet(students_file):
    repo = ExcelStudentRepository(students_file)

    assert repo.students("IS-231") == [Student("IS-231", "Иванов", "Иван"), Student("IS-231", "Петрова", "Анна")]
    assert repo.students("IS-232") == [Student("IS-232", "Сидоров", "Пётр")]


def test_empty_and_unknown_group_return_empty_list(students_file):
    repo = ExcelStudentRepository(students_file)

    assert repo.students("TI-251") == []
    assert repo.students("нет такой") == []


def test_display_name_is_last_then_first():
    assert Student("G", "Иванов", "Иван").display_name == "Иванов Иван"


def test_missing_file_raises_source_error(tmp_path):
    with pytest.raises(SourceError, match="students.xlsx"):
        ExcelStudentRepository(tmp_path / "students.xlsx")


def test_corrupted_file_raises_source_error(tmp_path):
    path = tmp_path / "students.xlsx"
    path.write_text("broken")

    with pytest.raises(SourceError):
        ExcelStudentRepository(path)
