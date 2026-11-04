"""Закрытие журнала, открытого в Microsoft Excel."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol


class WorkbookCloser(Protocol):
    def close(self, path: Path) -> bool:
        """Закрывает файл в стороннем приложении. True — если файл был найден и закрыт."""
        ...


class ExcelWorkbookCloser:
    """Находит книгу в запущенном Excel через COM и закрывает только её.

    Книга ищется в Running Object Table Windows, поэтому находится в любом
    из запущенных экземпляров Excel. Правки, которые пользователь успел
    внести в журнал, сохраняются. Остальные книги не трогаются; пустой
    Excel после этого завершается.
    """

    def close(self, path: Path) -> bool:
        try:
            import pythoncom
            import win32com.client
        except ImportError:
            return False

        target = os.path.normcase(os.path.abspath(path))
        pythoncom.CoInitialize()
        try:
            workbook = self._find_workbook(pythoncom, win32com.client, target)
            if workbook is None:
                return False
            excel = workbook.Application
            workbook.Close(SaveChanges=True)
            if excel.Workbooks.Count == 0:
                excel.Quit()
            return True
        except Exception:
            # Excel занят модальным диалогом или редактированием ячейки.
            return False
        finally:
            pythoncom.CoUninitialize()

    @staticmethod
    def _find_workbook(pythoncom, client, target: str):
        table = pythoncom.GetRunningObjectTable()
        context = pythoncom.CreateBindCtx(0)
        for moniker in table:
            try:
                name = moniker.GetDisplayName(context, None)
            except Exception:
                continue
            if os.path.normcase(name) == target:
                running = table.GetObject(moniker)
                return client.Dispatch(running.QueryInterface(pythoncom.IID_IDispatch))
        return None
