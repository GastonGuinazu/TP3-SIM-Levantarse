"""
Humo de interfaz PyQt5 (opcional). Se omite si PyQt5 no esta instalado.

  py -3.11 -m unittest tests.test_qa_ui_smoke -v
"""

from __future__ import annotations

import sys
import unittest

try:
    from PyQt5 import QtWidgets

    _PYQT = True
except ImportError:
    _PYQT = False

if _PYQT:
    from montecarloui import mainUi


@unittest.skipUnless(_PYQT, "PyQt5 no instalado; omitiendo humo de UI")
class TestHumoInterfaz(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QtWidgets.QApplication.instance():
            cls._app = QtWidgets.QApplication(sys.argv)
        else:
            cls._app = QtWidgets.QApplication.instance()

    def test_setup_ui_sin_excepcion_y_grilla_con_filas(self):
        w = QtWidgets.QMainWindow()
        try:
            ui = mainUi()
            ui.setupUi(w)
        finally:
            w.close()
        self.assertGreater(ui.tbl_vector.model().rowCount(), 0)
        self.assertEqual(ui.tbl_estrategias.rowCount(), 3)


if __name__ == "__main__":
    unittest.main()
