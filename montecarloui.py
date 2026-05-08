"""
Interfaz grafica PyQt5 — TP3 Montecarlo LEVANTARSE (Grupo 4K2).

Mapa rapido para la defensa con la profesora:
  - `VectorEstadoModel`: adapta la lista de filas (dicts) del simulador a una `QTableView`.
  - `TableVectorEstadoView`: misma tabla con opcion de anclar una fila debajo del encabezado.
  - `mainUi`: arma la ventana (parametros, tabla de estrategias, indicadores, vector de estado),
    valida entradas, ejecuta `SimuladorLevantarse` y refresca las tablas.

La logica del modelo y valores fijos por enunciado estan en `monte_carlos.py` y `funciones.py`.
"""

from PyQt5 import QtCore, QtGui, QtWidgets

from monte_carlos import ParametrosSimulacion, SimuladorLevantarse, validar_parametros_entrada


class VectorEstadoModel(QtCore.QAbstractTableModel):
    """
    Modelo de tabla para el vector de estado (muchas columnas, pocas filas visibles).

    Por que QAbstractTableModel: mejor rendimiento y menos parpadeo que rellenar QTableWidget
    celda a celda en cada simulacion. Las filas vienen ya armadas desde `SimuladorLevantarse.simular`.
    """

    # Indice de la columna "Dia" (primera); la UI ancla la fila solo con click ahi.
    COL_DIA = 0

    # Titulos de columnas en el mismo orden que `valores` en `data()` (claves del dict del simulador).
    columnas = [
        "Dia",
        "RND estrategia",
        "Estrategia",
        "RND despertar base",
        "T. despertar base",
        "RND rechazo",
        "Hubo rechazo",
        "T. despertar final",
        "RND pausa",
        "Hubo pausa",
        "T. pausa",
        "RND vestirse",
        "T. vestirse",
        "RND desayuno",
        "T. desayuno",
        "RND higiene",
        "T. higiene",
        "RND extra",
        "Hubo extra",
        "T. extra",
        "Tiempo total",
        "Tiempo total acum.",
        "Promedio acum.",
        "Max acum.",
        "Min acum.",
        "% pausa+extra acum.",
        "Cant. sin pausa/sin extra acum.",
        "% rechazo acum.",
        "% supera umbral acum.",
        "Cant. demora extra acum.",
        "T. demora extra acum.",
        "Prom. demora extra acum.",
    ]

    def __init__(self, filas=None, parent=None):
        super().__init__(parent)
        self._filas = filas or []

    def set_filas(self, filas):
        self.beginResetModel()
        self._filas = filas
        self.endResetModel()

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._filas)

    def columnCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.columnas)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or role != QtCore.Qt.DisplayRole:
            return None

        f = self._filas[index.row()]
        valores = [
            f["dia"],
            f'{f["rnd_estrategia"]:.4f}',
            f["estrategia"],
            f'{f["rnd_despertar_base"]:.4f}',
            f'{f["t_despertar_base"]:.2f}',
            "" if f["rnd_rechazo"] is None else f'{f["rnd_rechazo"]:.4f}',
            f["hubo_rechazo"],
            f'{f["t_despertar"]:.2f}',
            f'{f["rnd_pausa"]:.4f}',
            f["hubo_pausa"],
            f'{f["t_pausa"]:.2f}',
            f'{f["rnd_vestirse"]:.4f}',
            f'{f["t_vestirse"]:.2f}',
            f'{f["rnd_desayuno"]:.4f}',
            f'{f["t_desayuno"]:.2f}',
            f'{f["rnd_higiene"]:.4f}',
            f'{f["t_higiene"]:.2f}',
            f'{f["rnd_extra"]:.4f}',
            f["hubo_extra"],
            f'{f["t_extra"]:.2f}',
            f'{f["tiempo_total"]:.2f}',
            f'{f["tiempo_total_acum"]:.2f}',
            f'{f["tiempo_promedio_acum"]:.2f}',
            f'{f["tiempo_max_acum"]:.2f}',
            f'{f["tiempo_min_acum"]:.2f}',
            f'{f["porc_pausa_y_extra_acum"]:.2f}%',
            f["cant_sin_pausa_y_sin_extra_acum"],
            f'{f["porc_rechazo_acum"]:.2f}%',
            f'{f["porc_supera_umbral_acum"]:.2f}%',
            f["cant_demora_extra_acum"],
            f'{f["tiempo_demora_extra_acum"]:.2f}',
            f'{f["promedio_demora_extra_acum"]:.2f}',
        ]
        return str(valores[index.column()])

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            return self.columnas[section]
        return str(section + 1)


class FilaAncladaStripWidget(QtWidgets.QWidget):
    """Dibuja la fila fija en un hijo: QTableView a veces no expone paintEngine en el propio widget."""

    def __init__(self, view: "TableVectorEstadoView"):
        super().__init__(view)
        self._view = view
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setAutoFillBackground(False)
        self.hide()

    def paintEvent(self, event):
        view = self._view
        row_p = view._fila_anclada
        if row_p is None:
            return
        m = view.model()
        if m is None:
            return

        rh = self.height()
        painter = QtGui.QPainter(self)
        vh = view.verticalHeader()
        vhw = vh.width()
        hdr_rect = QtCore.QRect(0, 0, vhw, rh)
        vp = view.viewport().geometry()
        vh_geo = vh.geometry()
        x_datos0 = vp.left() - vh_geo.left()

        pal = view.palette()
        alt = view.alternatingRowColors() and (row_p % 2 == 1)
        bg = pal.alternateBase() if alt else pal.base()
        hl = pal.highlight()
        hl_txt = pal.color(QtGui.QPalette.HighlightedText)
        txt_col = pal.color(QtGui.QPalette.Text)
        grid = QtGui.QColor("#e2e8f0")

        painter.fillRect(hdr_rect, pal.button())
        painter.setPen(grid)
        painter.drawRect(hdr_rect)
        painter.setPen(txt_col)
        painter.drawText(hdr_rect, QtCore.Qt.AlignCenter, str(row_p + 1))

        sel = view.selectionModel()
        fm = view.fontMetrics()
        for col in range(m.columnCount()):
            idx = m.index(row_p, col)
            w = view.columnWidth(col)
            x = x_datos0 + view.columnViewportPosition(col)
            cell = QtCore.QRect(x, 0, w, rh)
            selected = sel is not None and sel.isSelected(idx)
            painter.fillRect(cell, hl if selected else bg)
            painter.setPen(grid)
            painter.drawRect(cell)
            texto = str(m.data(idx, QtCore.Qt.DisplayRole) or "")
            painter.setPen(hl_txt if selected else txt_col)
            pad = 6
            painter.drawText(
                cell.adjusted(pad, 0, -pad, 0),
                QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                fm.elidedText(texto, QtCore.Qt.ElideRight, cell.width() - 2 * pad),
            )


class TableVectorEstadoView(QtWidgets.QTableView):
    """
    Una sola tabla: la fila anclada sigue en su lugar y ademas se repinta fija debajo
    del encabezado horizontal (sin segunda grilla ni segundo encabezado).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fila_anclada = None
        self._strip = FilaAncladaStripWidget(self)
        self.horizontalScrollBar().valueChanged.connect(self._strip.update)
        self.horizontalHeader().sectionResized.connect(lambda *a: self._strip.update())

    def set_fila_anclada(self, row):
        """row es indice de modelo (0-based) o None para desactivar."""
        self._fila_anclada = row
        if row is None:
            self._strip.hide()
        else:
            self._sync_strip_geometry()
            self._strip.show()
            self._ordenar_capas_fila_anclada()
        self.updateGeometries()
        if row is not None:
            QtCore.QTimer.singleShot(0, self._sync_strip_geometry)
        self.update()

    def fila_anclada(self):
        return self._fila_anclada

    def _sync_strip_geometry(self):
        if self._fila_anclada is None:
            return
        rh = self._altura_fila_datos()
        hh = self.horizontalHeader().geometry()
        y = hh.bottom() + 1
        vh = self.verticalHeader().geometry()
        self._strip.setGeometry(vh.left(), y, max(0, self.width() - vh.left()), rh)

    def _ordenar_capas_fila_anclada(self):
        """La franja va sobre el viewport pero debajo del encabezado horizontal (no lo tapa)."""
        self._strip.raise_()
        self.horizontalHeader().raise_()

    def _altura_fila_datos(self):
        m = self.model()
        if m is None:
            return max(22, self.verticalHeader().defaultSectionSize())
        for r in range(m.rowCount()):
            h = self.rowHeight(r)
            if h > 0:
                return h
        h = self.sizeHintForRow(0)
        return h if h > 0 else self.verticalHeader().defaultSectionSize()

    def updateGeometries(self):
        """
        QTableView recalcula margenes internos al hacer scroll/resize/reset.
        Si hay fila anclada, re-ubicamos la franja fija.
        """
        super().updateGeometries()
        if self._fila_anclada is None:
            return
        self._sync_strip_geometry()
        self._strip.show()
        self._ordenar_capas_fila_anclada()

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        if self._fila_anclada is None:
            return
        self._sync_strip_geometry()
        self._strip.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._fila_anclada is not None:
            self._sync_strip_geometry()
            self._ordenar_capas_fila_anclada()


class mainUi(object):
    """
    Controlador visual del TP: crea widgets, conecta senales y orquesta una corrida Montecarlo.

    Convencion de metodos:
      - `_crear_*`: construye un bloque de la interfaz.
      - `_cargar_*`: vuelca datos del simulador en tablas.
      - `_build_params` / `_validar`: puente entre spinboxes y `ParametrosSimulacion`.
    """

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1500, 860)
        MainWindow.setWindowTitle("TP3 - Montecarlo LEVANTARSE - Grupo 1 4K2")
        MainWindow.setMinimumSize(1000, 640)

        self._fila_anclada = None

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)
        layout_base = QtWidgets.QVBoxLayout(self.centralwidget)
        layout_base.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        layout_base.addWidget(self.scroll_area)

        self.content_widget = QtWidgets.QWidget()
        self.scroll_area.setWidget(self.content_widget)

        layout_principal = QtWidgets.QVBoxLayout(self.content_widget)
        layout_principal.setContentsMargins(10, 10, 10, 10)
        layout_principal.setSpacing(8)

        fuente = MainWindow.font()
        fuente.setPointSize(10)
        MainWindow.setFont(fuente)
        MainWindow.setStyleSheet(
            "QWidget { background-color: #f8fafc; color: #1f2937; }"
            "QGroupBox {"
            "  font-weight: 700;"
            "  border: 1px solid #d6deeb;"
            "  border-radius: 8px;"
            "  margin-top: 8px;"
            "  padding-top: 8px;"
            "  background-color: #ffffff;"
            "}"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #0f172a; }"
            "QPushButton {"
            "  background-color: #2563eb;"
            "  color: white;"
            "  border: none;"
            "  border-radius: 6px;"
            "  padding: 6px 14px;"
            "  font-weight: 700;"
            "}"
            "QPushButton:hover { background-color: #1d4ed8; }"
            "QPushButton:pressed { background-color: #1e40af; }"
            "QSpinBox, QDoubleSpinBox {"
            "  background-color: #ffffff;"
            "  border: 1px solid #cbd5e1;"
            "  border-radius: 5px;"
            "  padding: 3px;"
            "}"
            "QHeaderView::section {"
            "  background-color: #e2e8f0;"
            "  color: #0f172a;"
            "  padding: 4px;"
            "  font-weight: 700;"
            "  border: 1px solid #cbd5e1;"
            "}"
            "QTableView, QTableWidget {"
            "  background-color: #ffffff;"
            "  gridline-color: #e2e8f0;"
            "  selection-background-color: #bfdbfe;"
            "  selection-color: #0f172a;"
            "}"
        )

        self._crear_panel_parametros(layout_principal)
        layout_resumen = QtWidgets.QHBoxLayout()
        layout_resumen.setSpacing(8)
        self._crear_tabla_estrategias(layout_resumen)
        self._crear_tabla_indicadores(layout_resumen)
        layout_resumen.setStretch(0, 1)
        layout_resumen.setStretch(1, 1)
        layout_principal.addLayout(layout_resumen)
        self._crear_vector_estado(layout_principal)
        layout_principal.setStretch(0, 0)
        layout_principal.setStretch(1, 1)
        layout_principal.setStretch(2, 3)

        self.btn_simular.clicked.connect(self.simular)
        self.simular()

    def _crear_panel_parametros(self, parent_layout):
        """Spinboxes y boton Simular: parametros configurables de `ParametrosSimulacion`."""
        box = QtWidgets.QGroupBox("Parametros de simulacion")
        form = QtWidgets.QGridLayout(box)

        self.spn_dias = QtWidgets.QSpinBox()
        self.spn_dias.setRange(1, 1_000_000)
        self.spn_dias.setValue(100000)

        self.spn_fila_desde = QtWidgets.QSpinBox()
        self.spn_fila_desde.setRange(1, 1_000_000)
        self.spn_fila_desde.setValue(1)

        self.spn_umbral = QtWidgets.QDoubleSpinBox()
        self.spn_umbral.setRange(0.0, 10_000.0)
        self.spn_umbral.setDecimals(2)
        self.spn_umbral.setValue(45.0)

        self.spn_seed = QtWidgets.QSpinBox()
        self.spn_seed.setRange(0, 999_999_999)
        self.spn_seed.setValue(42)

        self.spn_prob_extra = self._nuevo_prob(0.25)

        self.spn_pausa_min = self._nuevo_tiempo(5.0)
        self.spn_pausa_max = self._nuevo_tiempo(7.0)
        self.spn_act_min = self._nuevo_tiempo(5.0)
        self.spn_act_max = self._nuevo_tiempo(10.0)
        self.spn_media_extra = self._nuevo_tiempo(8.0)

        # En el PDF: imprevisto / juguete perdido — 25% de los dias, tiempo ~ Exp(media).
        self.spn_prob_extra.setToolTip(
            "Probabilidad de que ese dia ocurra la demora extra del enunciado "
            "(imprevisto, objeto perdido, etc.). Por defecto 0,25 = 25 de 100 dias."
        )
        self.spn_media_extra.setToolTip(
            "Media (en minutos) de la distribucion exponencial de la demora extra. "
            "En el enunciado la media es 8 minutos."
        )

        controles = [
            ("Dias a simular (N)", self.spn_dias),
            ("Fila inicial del vector (i)", self.spn_fila_desde),
            ("Umbral de tardanza (min)", self.spn_umbral),
            ("Semilla", self.spn_seed),
            ("P(Demora extra)", self.spn_prob_extra),
            ("Media demora extra exp.", self.spn_media_extra),
            ("Pausa U(min)", self.spn_pausa_min),
            ("Pausa U(max)", self.spn_pausa_max),
            ("Actividad U(min)", self.spn_act_min),
            ("Actividad U(max)", self.spn_act_max),
        ]

        for i, (texto, control) in enumerate(controles):
            form.addWidget(QtWidgets.QLabel(texto), i // 3, (i % 3) * 2)
            form.addWidget(control, i // 3, (i % 3) * 2 + 1)

        self.btn_simular = QtWidgets.QPushButton("Simular")
        self.lbl_info = QtWidgets.QLabel("")
        self.lbl_info.setStyleSheet("color: #334155; font-weight: 700;")
        fila_boton = (len(controles) - 1) // 3 + 1
        form.addWidget(self.btn_simular, fila_boton, 0, 1, 1)
        form.addWidget(self.lbl_info, fila_boton, 1, 1, 5)

        parent_layout.addWidget(box)

    @staticmethod
    def _nuevo_prob(valor):
        """Spinbox en [0,1] para P(demora extra)."""
        spn = QtWidgets.QDoubleSpinBox()
        spn.setRange(0.0, 1.0)
        spn.setDecimals(4)
        spn.setSingleStep(0.01)
        spn.setValue(valor)
        return spn

    @staticmethod
    def _nuevo_tiempo(valor):
        """Spinbox para minutos (pausa, actividades, media demora extra)."""
        spn = QtWidgets.QDoubleSpinBox()
        spn.setRange(0.0, 10_000.0)
        spn.setDecimals(2)
        spn.setSingleStep(0.1)
        spn.setValue(valor)
        return spn

    def _crear_tabla_estrategias(self, parent_layout):
        """Muestra P, P acumulada y rangos de RND para el sorteo de estrategia (Montecarlo)."""
        box = QtWidgets.QGroupBox("Distribucion de estrategias de despertar")
        box.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        layout = QtWidgets.QVBoxLayout(box)
        self.tbl_estrategias = QtWidgets.QTableWidget()
        self.tbl_estrategias.setMinimumHeight(0)
        self.tbl_estrategias.setMaximumHeight(16_777_215)
        self.tbl_estrategias.setColumnCount(5)
        self.tbl_estrategias.setHorizontalHeaderLabels(
            ["Estrategia", "Probabilidad", "Acumulada", "RND desde", "RND hasta"]
        )
        self.tbl_estrategias.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tbl_estrategias.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tbl_estrategias.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.tbl_estrategias.setAlternatingRowColors(True)
        self.tbl_estrategias.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tbl_estrategias.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tbl_estrategias.horizontalHeader().setStretchLastSection(False)
        self.tbl_estrategias.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.tbl_estrategias.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.tbl_estrategias)
        parent_layout.addWidget(box)

    def _crear_tabla_indicadores(self, parent_layout):
        """Resumen numerico: preguntas 1 a 5 del enunciado + tres variables extra del grupo."""
        box = QtWidgets.QGroupBox("Indicadores finales del TP")
        box.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        layout = QtWidgets.QVBoxLayout(box)
        self.tbl_indicadores = QtWidgets.QTableWidget()
        self.tbl_indicadores.setMinimumHeight(0)
        self.tbl_indicadores.setMaximumHeight(16_777_215)
        self.tbl_indicadores.setColumnCount(2)
        self.tbl_indicadores.setHorizontalHeaderLabels(["Indicador", "Valor"])
        self.tbl_indicadores.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tbl_indicadores.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tbl_indicadores.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.tbl_indicadores.setAlternatingRowColors(True)
        self.tbl_indicadores.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tbl_indicadores.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tbl_indicadores.horizontalHeader().setStretchLastSection(False)
        self.tbl_indicadores.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.tbl_indicadores.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        layout.addWidget(self.tbl_indicadores)
        parent_layout.addWidget(box)

    def _crear_vector_estado(self, parent_layout):
        """
        Grilla principal del TP: cada fila es un dia con RND, tiempos y acumuladores.
        Cumple requisitos de scroll, encabezados fijos y copia a Excel (Ctrl+C).
        """
        box = QtWidgets.QGroupBox("Vector de estado (200 filas desde i, mas fila N)")
        box.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        layout = QtWidgets.QVBoxLayout(box)

        fila_ref = QtWidgets.QHBoxLayout()
        self.lbl_fila_anclada = QtWidgets.QLabel(
            "Para anclar una fila, hace click en la columna Dia; en las demas columnas solo seleccionas sin anclar."
        )
        self.lbl_fila_anclada.setWordWrap(True)
        self.lbl_fila_anclada.setStyleSheet("color: #475569; font-size: 9pt;")
        fila_ref.addWidget(self.lbl_fila_anclada, 1)
        self.btn_quitar_ancla = QtWidgets.QPushButton("Quitar ancla")
        self.btn_quitar_ancla.setVisible(False)
        self.btn_quitar_ancla.clicked.connect(self._limpiar_fila_anclada)
        fila_ref.addWidget(self.btn_quitar_ancla, 0, QtCore.Qt.AlignTop)
        layout.addLayout(fila_ref)

        self.vector_model = VectorEstadoModel([])
        self.tbl_vector = TableVectorEstadoView()
        self.tbl_vector.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.tbl_vector.setMinimumHeight(300)
        self.tbl_vector.setModel(self.vector_model)
        self.tbl_vector.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.tbl_vector.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tbl_vector.setAlternatingRowColors(True)
        self.tbl_vector.setSortingEnabled(False)
        self.tbl_vector.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tbl_vector.horizontalHeader().setStretchLastSection(True)
        self.tbl_vector.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.tbl_vector.verticalHeader().setVisible(True)
        self.tbl_vector.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tbl_vector.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tbl_vector.setWordWrap(False)
        self.tbl_vector.clicked.connect(self._on_vector_clicked)
        layout.addWidget(self.tbl_vector)
        parent_layout.addWidget(box, 1)

        self._configurar_copia_excel()

    def _on_vector_clicked(self, index):
        if not index.isValid():
            return
        if index.column() != VectorEstadoModel.COL_DIA:
            return
        self._establecer_fila_anclada(index.row())

    def _establecer_fila_anclada(self, row):
        n = self.vector_model.rowCount()
        if row < 0 or row >= n:
            return
        self._fila_anclada = row
        self.tbl_vector.set_fila_anclada(row)
        self.btn_quitar_ancla.setVisible(True)
        self.lbl_fila_anclada.setText(
            f"Fila anclada (fila {row + 1}). El titulo de columnas sigue fijo; la fila queda debajo al hacer scroll vertical."
        )

    def _limpiar_fila_anclada(self):
        self._fila_anclada = None
        self.tbl_vector.set_fila_anclada(None)
        self.btn_quitar_ancla.setVisible(False)
        self.lbl_fila_anclada.setText(
            "Para anclar una fila, hace click en la columna Dia; en las demas columnas solo seleccionas sin anclar."
        )

    def _configurar_copia_excel(self):
        """Ctrl+C copia la seleccion de la tabla con foco (texto separado por tabs, listo para Excel)."""
        self._atajo_copiar = QtWidgets.QShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_C, self.centralwidget)
        self._atajo_copiar.activated.connect(self._copiar_seleccion_activa)

    @staticmethod
    def _ajustar_alto_tabla_widget(tabla):
        """
        Ajusta altura exacta de la tabla para evitar zona gris sobrante bajo las filas.
        """
        alto = tabla.horizontalHeader().height()
        for fila in range(tabla.rowCount()):
            alto += tabla.rowHeight(fila)
        if tabla.horizontalScrollBar().isVisible():
            alto += tabla.horizontalScrollBar().height()
        alto += tabla.frameWidth() * 2 + 2
        min_alto = tabla.horizontalHeader().height() + tabla.frameWidth() * 2 + 8
        tabla.setFixedHeight(max(alto, min_alto))

    def _copiar_seleccion_activa(self):
        """Enruta el atajo al QTableView o QTableWidget que tenga el foco."""
        widget = self.centralwidget.focusWidget()
        if widget is self.tbl_vector:
            self._copiar_table_view(widget)
            return
        if widget in (self.tbl_estrategias, self.tbl_indicadores):
            self._copiar_table_widget(widget)

    @staticmethod
    def _copiar_table_widget(tabla):
        rangos = tabla.selectedRanges()
        if not rangos:
            return
        r = rangos[0]
        filas = []
        for fila in range(r.topRow(), r.bottomRow() + 1):
            valores = []
            for col in range(r.leftColumn(), r.rightColumn() + 1):
                item = tabla.item(fila, col)
                valores.append(item.text() if item else "")
            filas.append("\t".join(valores))
        QtWidgets.QApplication.clipboard().setText("\n".join(filas))

    @staticmethod
    def _copiar_table_view(tabla):
        indices = tabla.selectionModel().selectedIndexes()
        if not indices:
            return
        por_fila = {}
        for idx in indices:
            por_fila.setdefault(idx.row(), {})[idx.column()] = idx.data() or ""
        filas = []
        for fila in sorted(por_fila.keys()):
            cols = por_fila[fila]
            valores = [str(cols.get(c, "")) for c in range(min(cols.keys()), max(cols.keys()) + 1)]
            filas.append("\t".join(valores))
        QtWidgets.QApplication.clipboard().setText("\n".join(filas))

    def _build_params(self):
        """Lee la UI y construye el dataclass que consume `SimuladorLevantarse`."""
        return ParametrosSimulacion(
            dias=int(self.spn_dias.value()),
            fila_desde=int(self.spn_fila_desde.value()),
            umbral_tarde=float(self.spn_umbral.value()),
            seed=int(self.spn_seed.value()),
            pausa_min=float(self.spn_pausa_min.value()),
            pausa_max=float(self.spn_pausa_max.value()),
            actividad_min=float(self.spn_act_min.value()),
            actividad_max=float(self.spn_act_max.value()),
            prob_demora_extra=float(self.spn_prob_extra.value()),
            media_demora_extra=float(self.spn_media_extra.value()),
        )

    @staticmethod
    def _validar(p: ParametrosSimulacion):
        """Delega en `validar_parametros_entrada` (compartido con tests sin PyQt)."""
        return validar_parametros_entrada(p)

    def simular(self):
        """Disparado al iniciar y al pulsar Simular: valida, corre Montecarlo y actualiza tablas."""
        params = self._build_params()
        error = self._validar(params)
        if error:
            QtWidgets.QMessageBox.critical(None, "Error de parametros", error)
            return

        simulador = SimuladorLevantarse(params)
        resultados = simulador.simular()
        self._cargar_estrategias(resultados["estrategias"])
        self._cargar_indicadores(resultados["indicadores"])
        self.vector_model.set_filas(resultados["filas"])
        if self._fila_anclada is not None:
            if self._fila_anclada < self.vector_model.rowCount():
                self._establecer_fila_anclada(self._fila_anclada)
            else:
                self._limpiar_fila_anclada()
        self.lbl_info.setText(
            f"Simulacion completada: {params.dias} dias. "
            f"Vector visible: 200 filas desde {params.fila_desde}, mas fila N."
        )

    def _cargar_estrategias(self, estrategias):
        """Llena la tabla de distribucion de estrategias (salida de `_crear_distribucion_estrategias`)."""
        self.tbl_estrategias.setUpdatesEnabled(False)
        self.tbl_estrategias.setRowCount(len(estrategias))
        for row, d in enumerate(estrategias):
            valores = [
                d["estrategia"],
                f'{d["probabilidad"]:.4f}',
                f'{d["acumulada"]:.4f}',
                f'{d["rnd_desde"]:.4f}',
                f'{d["rnd_hasta"] - 0.0001:.4f}',
            ]
            for col, valor in enumerate(valores):
                self.tbl_estrategias.setItem(row, col, QtWidgets.QTableWidgetItem(str(valor)))
        self.tbl_estrategias.resizeRowsToContents()
        self._ajustar_alto_tabla_widget(self.tbl_estrategias)
        self.tbl_estrategias.setUpdatesEnabled(True)

    def _cargar_indicadores(self, indicadores):
        """Traduce el dict `indicadores` del simulador a filas legibles para la profesora."""
        filas = [
            ("1) Tiempo promedio de preparar a Luna", f'{indicadores["tiempo_promedio"]:.2f} min'),
            (
                "2) % de dias con pausa y juguete perdido (demora extra)",
                f'{indicadores["porcentaje_pausa_y_extra"]:.2f}%',
            ),
            (
                "3) Cantidad de dias sin pausa y sin juguete perdido",
                str(indicadores["cantidad_sin_pausa_y_sin_extra"]),
            ),
            ("4) Tiempo maximo de preparar a Luna", f'{indicadores["tiempo_maximo"]:.2f} min'),
            ("5) Tiempo minimo de preparar a Luna", f'{indicadores["tiempo_minimo"]:.2f} min'),
            (
                "6.a) % de dias con reaccion lenta al despertar",
                f'{indicadores["porcentaje_rechazo"]:.2f}%',
            ),
            (
                "6.b) % de dias que superan el umbral de tardanza",
                f'{indicadores["porcentaje_supera_umbral"]:.2f}%',
            ),
            (
                "6.c) Promedio de demora extra cuando ocurre",
                f'{indicadores["promedio_demora_extra_si_ocurre"]:.2f} min',
            ),
        ]

        self.tbl_indicadores.setUpdatesEnabled(False)
        self.tbl_indicadores.setRowCount(len(filas))
        for row, (k, v) in enumerate(filas):
            self.tbl_indicadores.setItem(row, 0, QtWidgets.QTableWidgetItem(k))
            self.tbl_indicadores.setItem(row, 1, QtWidgets.QTableWidgetItem(v))
        self.tbl_indicadores.resizeRowsToContents()
        self._ajustar_alto_tabla_widget(self.tbl_indicadores)
        self.tbl_indicadores.setUpdatesEnabled(True)
