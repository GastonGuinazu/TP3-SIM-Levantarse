"""
Punto de entrada de la aplicacion de escritorio (TP3 LEVANTARSE).

Flujo:
  1. Crea `QApplication` (requerido por Qt para eventos y ventanas).
  2. Instancia `QMainWindow` y le delega el layout a `mainUi.setupUi` (ver `montecarloui.py`).
  3. Muestra la ventana y entra al loop de eventos hasta cerrar la app.

La logica de simulacion NO esta aqui: solo el arranque minimo de la GUI.
"""

from montecarloui import mainUi
from PyQt5 import QtWidgets
import sys


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = mainUi()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
