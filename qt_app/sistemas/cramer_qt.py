from PySide6.QtWidgets import (\r\n    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,\r\n    QScrollArea, QGridLayout, QLineEdit, QTextEdit, QMessageBox, QSlider,\r\n    QToolButton, QMenu, QDialog, QDialogButtonBox, QPlainTextEdit\r\n)
from PySide6.QtCore import Qt, QSize
from ..theme import install_toggle_shortcut, bind_font_scale_stylesheet, scaled_font_px, bind_theme_icon, make_overflow_icon, gear_icon_preferred
from ..settings_qt import open_settings_dialog
from fractions import Fraction
from qt_app.matrices_qt import determinante_con_pasos as determinante_con_pasos_ascii
import re


def _fmt_fraction(x: Fraction) -> str:
    try:
        if isinstance(x, Fraction):
            if x.denominator == 1:
                return str(x.numerator)
            return f"{x.numerator}/{x.denominator}"
        return str(x)
    except Exception:
        return str(x)



class DetallesDeterminantesWindow(QMainWindow):
    """Ventana que muestra los procedimientos de determinantes uno por uno con navegación."""
    def __init__(self, parent=None, items=None):
        super().__init__(parent)
        self.setWindowTitle("Cálculos de determinantes")
        self.items = items or []  # lista de (titulo, lineas[])
        self.index = 0

        outer = QWidget()
        self.setCentralWidget(outer)
        lay = QVBoxLayout(outer)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        self.header = QLabel("")
        self.header.setAlignment(Qt.AlignCenter)
        bind_font_scale_stylesheet(
            self.header,
            "font-weight:700; font-size:{body}px;",
            body=14,
        )
        lay.addWidget(self.header)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        bind_font_scale_stylesheet(
            self.text,
            "font-family:Consolas,monospace;font-size:{body}px;",
            body=12,
        )
        lay.addWidget(self.text, 1)

        btns = QHBoxLayout()
        self.prev_btn = QPushButton("Anterior")
        self.next_btn = QPushButton("Siguiente")
        self.close_btn = QPushButton("Cerrar")
        btns.addWidget(self.prev_btn)
        btns.addWidget(self.next_btn)
        btns.addStretch(1)
        btns.addWidget(self.close_btn)
        lay.addLayout(btns)

        self.prev_btn.clicked.connect(self._prev)
        self.next_btn.clicked.connect(self._next)
        self.close_btn.clicked.connect(self.close)

        self._update_view()

    def _update_view(self):
        if not self.items:
            self.header.setText("No hay cálculos disponibles")
            self.text.setPlainText("")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return
        title, lines = self.items[self.index]
        self.header.setText(title)
        self.text.setPlainText("\n".join(lines))
        self.prev_btn.setEnabled(self.index > 0)
        self.next_btn.setEnabled(self.index < len(self.items) - 1)

    def _next(self):
        if self.index < len(self.items) - 1:
            self.index += 1
            self._update_view()

    def _prev(self):
        if self.index > 0:
            self.index -= 1
            self._update_view()



class CramerWindow(QMainWindow):
    """Interfaz para resolver sistemas por el método de Cramer.

    La cuadrícula de entrada es igual a la de Gauss-Jordan: una matriz aumentada
    con n filas y n+1 columnas. El método exige que n == columnas-1.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Método de Cramer")
        self._entries = []
        self._rows = 3
        self._cols_no_b = 3

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(18)

        card = QFrame()
        card.setObjectName("Card")
        outer.addWidget(card)
        main = QVBoxLayout(card)
        main.setContentsMargins(24, 24, 24, 24)
        main.setSpacing(16)

        top = QHBoxLayout()
        main.addLayout(top)
        self.btn_back = QPushButton("Volver")
        self.btn_back.clicked.connect(self._go_back)
        top.addWidget(self.btn_back)
        top.addSpacing(24)
        row_container = QWidget()
        row_layout = QVBoxLayout(row_container)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)
        row_label = QLabel("Filas")
        row_label.setAlignment(Qt.AlignHCenter)
        row_layout.addWidget(row_label)
        row_controls = QHBoxLayout()
        row_controls.setContentsMargins(0, 0, 0, 0)
        row_controls.setSpacing(6)
        self.row_slider = QSlider(Qt.Horizontal)
        self.row_slider.setRange(1, 12)
        self.row_slider.setSingleStep(1)
        self.row_slider.setPageStep(1)
        self.row_slider.setTickInterval(1)
        self.row_slider.setTickPosition(QSlider.TicksBelow)
        self.row_slider.setValue(self._rows)
        self.row_slider.valueChanged.connect(self._on_rows_changed)
        self.row_slider.setFixedWidth(160)
        row_controls.addWidget(self.row_slider, 1)
        self.row_value_label = QLabel(str(self._rows))
        self.row_value_label.setFixedWidth(32)
        self.row_value_label.setAlignment(Qt.AlignCenter)
        row_controls.addWidget(self.row_value_label)
        row_layout.addLayout(row_controls)
        top.addWidget(row_container)
        top.addSpacing(18)
        more_btn = QToolButton()
        more_btn.setAutoRaise(True)
        more_btn.setCursor(Qt.PointingHandCursor)
        more_btn.setToolTip('M�s opciones')
        more_btn.setPopupMode(QToolButton.InstantPopup)
        try:
            bind_theme_icon(more_btn, make_overflow_icon, 20)
            more_btn.setIconSize(QSize(20, 20))
        except Exception:
            pass
        menu = QMenu(more_btn)
        act_settings = menu.addAction(gear_icon_preferred(22), 'Configuraci�n')
        act_settings.triggered.connect(self._open_settings)
        more_btn.setMenu(menu)
        top.addWidget(more_btn)
        col_container = QWidget()
        col_layout = QVBoxLayout(col_container)
        col_layout.setContentsMargins(0, 0, 0, 0)
        col_layout.setSpacing(4)
        col_label = QLabel("Columnas")
        col_label.setAlignment(Qt.AlignHCenter)
        col_layout.addWidget(col_label)
        col_controls = QHBoxLayout()
        col_controls.setContentsMargins(0, 0, 0, 0)
        col_controls.setSpacing(6)
        self.col_slider = QSlider(Qt.Horizontal)
        self.col_slider.setRange(1, 12)
        self.col_slider.setSingleStep(1)
        self.col_slider.setPageStep(1)
        self.col_slider.setTickInterval(1)
        self.col_slider.setTickPosition(QSlider.TicksBelow)
        self.col_slider.setValue(self._cols_no_b)
        self.col_slider.valueChanged.connect(self._on_cols_changed)
        self.col_slider.setFixedWidth(160)
        col_controls.addWidget(self.col_slider, 1)
        self.col_value_label = QLabel(str(self._cols_no_b))
        self.col_value_label.setFixedWidth(32)
        self.col_value_label.setAlignment(Qt.AlignCenter)
        col_controls.addWidget(self.col_value_label)
        col_layout.addLayout(col_controls)
        top.addWidget(col_container)
        top.addSpacing(24)
        self.btn_limpiar = QPushButton("Limpiar pantalla")
        self.btn_limpiar.clicked.connect(self._limpiar)
        top.addWidget(self.btn_limpiar)
        # nueva opción: ingreso por ecuaciones (texto)
        self.btn_ingresar_ecuaciones = QPushButton("Ingresar ecuaciones")
        self.btn_ingresar_ecuaciones.clicked.connect(self._open_ecuaciones_dialog)
        top.addWidget(self.btn_ingresar_ecuaciones)
        top.addSpacing(18)
        more_btn = QToolButton()
        more_btn.setAutoRaise(True)
        more_btn.setCursor(Qt.PointingHandCursor)
        more_btn.setToolTip('M�s opciones')
        more_btn.setPopupMode(QToolButton.InstantPopup)
        try:
            bind_theme_icon(more_btn, make_overflow_icon, 20)
            more_btn.setIconSize(QSize(20, 20))
        except Exception:
            pass
        menu = QMenu(more_btn)
        act_settings = menu.addAction(gear_icon_preferred(22), 'Configuraci�n')
        act_settings.triggered.connect(self._open_settings)
        more_btn.setMenu(menu)
        top.addWidget(more_btn)
        # Ajuste: bot�n de configuraci�n reemplazado por men� ?
        top.addStretch(1)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        main.addWidget(self.scroll)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setHorizontalSpacing(10)
        self.grid_layout.setVerticalSpacing(8)
        self.scroll.setWidget(self.grid_container)

        title = QLabel("Resultados")
        title.setObjectName("Subtitle")
        main.addWidget(title)

        # Área de resultados: cuadro destacado con det(A) y valores de las variables
        self.result_highlight = QFrame()
        self.result_highlight.setObjectName("Card")
        rh_lay = QVBoxLayout(self.result_highlight)
        rh_lay.setContentsMargins(12, 12, 12, 12)
        rh_lay.setSpacing(8)
        self.det_label = QLabel("det(A) = —")
        bind_font_scale_stylesheet(
            self.det_label,
            "font-size:{title}px;font-weight:700;color:#b91c1c;",
            title=18,
        )
        rh_lay.addWidget(self.det_label)
        self.vars_box = QTextEdit()
        self.vars_box.setReadOnly(True)
        bind_font_scale_stylesheet(
            self.vars_box,
            "font-size:{body}px;font-weight:700;background:transparent;border:none;font-family:Segoe UI;",
            body=16,
        )
        rh_lay.addWidget(self.vars_box)
        main.addWidget(self.result_highlight)

        # Botón resolver
        self.btn_resolver = QPushButton("Resolver por Cramer")
        self.btn_resolver.clicked.connect(self._resolver)
        self.btn_resolver.setEnabled(False)
        main.addWidget(self.btn_resolver)

        # Panel de procedimiento (alto nivel) y panel ocultable para cálculos de determinantes
        self.procedimiento = QTextEdit()
        self.procedimiento.setReadOnly(True)
        bind_font_scale_stylesheet(
            self.procedimiento,
            "font-family:Segoe UI; font-size:{body}px;",
            body=12,
        )
        main.addWidget(self.procedimiento, 1)

        self.toggle_det_btn = QPushButton("Mostrar cálculos de determinantes")
        self.toggle_det_btn.setCheckable(True)
        self.toggle_det_btn.clicked.connect(self._open_detalles_window)
        main.addWidget(self.toggle_det_btn)

        self.detalles_container = QFrame()
        self.detalles_container.setVisible(False)
        det_l = QVBoxLayout(self.detalles_container)
        det_l.setContentsMargins(6, 6, 6, 6)
        self.detalles_text = QTextEdit()
        self.detalles_text.setReadOnly(True)
        bind_font_scale_stylesheet(
            self.detalles_text,
            "font-family:Consolas,monospace;font-size:{body}px;",
            body=12,
        )
        det_l.addWidget(self.detalles_text)
        main.addWidget(self.detalles_container, 1)

        self._rebuild_grid(self._rows, self._cols_no_b + 1)
        install_toggle_shortcut(self)

    def _go_back(self):
        try:
            p = self.parent()
            self.close()
            if p is not None:
                p.show()
                p.activateWindow()
        except Exception:
            self.close()

    def _limpiar(self):
        self._entries = []
        while self.grid_layout.count():
            w = self.grid_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.procedimiento.clear()
        self.detalles_text.clear()
        self.det_label.setText("det(A) = —")
        self.vars_box.clear()
        self.btn_resolver.setEnabled(False)

    def _rebuild_grid(self, filas: int, columnas: int):
        old = [[e.text() for e in row] for row in self._entries] if self._entries else []
        self._limpiar()
        # encabezados para variables x1..xn y columna b
        for j in range(columnas - 1):
            h = QLabel(f"x{j+1}")
            h.setStyleSheet("font-weight:700;")
            self.grid_layout.addWidget(h, 0, j)
        hb = QLabel("b")
        hb.setStyleSheet("font-weight:700;")
        self.grid_layout.addWidget(hb, 0, columnas - 1)
        self._entries = []
        for i in range(filas):
            row = []
            for j in range(columnas):
                e = QLineEdit()
                e.setPlaceholderText("0")
                e.setAlignment(Qt.AlignCenter)
                if old and i < len(old) and j < len(old[i]):
                    e.setText(old[i][j])
                try:
                    e.textChanged.connect(self._preview_sistema)
                except Exception:
                    pass
                self.grid_layout.addWidget(e, i + 1, j)
                row.append(e)
            self._entries.append(row)
        self.btn_resolver.setEnabled(True)
        # Vista previa inicial
        self._preview_sistema()

    def _on_rows_changed(self, value: int):
        value = max(1, value)
        self.row_value_label.setText(str(value))
        if value == self._rows:
            return
        self._rows = value
        self._rebuild_grid(self._rows, self._cols_no_b + 1)

    def _on_cols_changed(self, value: int):
        value = max(1, value)
        self.col_value_label.setText(str(value))
        if value == self._cols_no_b:
            return
        self._cols_no_b = value
        self._rebuild_grid(self._rows, self._cols_no_b + 1)

    # --- ingreso por ecuaciones (nuevo) ---
    def _open_ecuaciones_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Ingresar ecuaciones")
        lay = QVBoxLayout(dlg)
        info = QLabel("Ingrese una ecuación por línea. Ejemplo: 2x + 3y = 5\nUse variables como x, y, z o x1, x2...")
        info.setWordWrap(True)
        lay.addWidget(info)
        editor = QPlainTextEdit()
        editor.setPlaceholderText("Ej:\n2x + 3y = 5\n-x + 4y = 1")
        lay.addWidget(editor, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        lay.addWidget(buttons)
        if dlg.exec() != QDialog.Accepted:
            return
        text = editor.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Vacío", "No ingresaste ecuaciones.")
            return
        try:
            M = self._parse_equations_text(text, self._cols_no_b)
        except Exception as exc:
            QMessageBox.critical(self, "Error de parseo", f"No se pudieron interpretar las ecuaciones: {exc}")
            return
        filas = len(M)
        columnas = len(M[0]) if filas else 0
        if filas == 0:
            QMessageBox.warning(self, "Error", "No se detectaron ecuaciones válidas.")
            return
        self._rows = filas
        self._cols_no_b = columnas - 1
        if self.row_slider.maximum() < self._rows:
            self.row_slider.setMaximum(self._rows)
        if self.col_slider.maximum() < self._cols_no_b:
            self.col_slider.setMaximum(self._cols_no_b)
        self.row_slider.blockSignals(True)
        self.row_slider.setValue(self._rows)
        self.row_slider.blockSignals(False)
        self.row_value_label.setText(str(self._rows))
        self.col_slider.blockSignals(True)
        self.col_slider.setValue(self._cols_no_b)
        self.col_slider.blockSignals(False)
        self.col_value_label.setText(str(self._cols_no_b))
        self._rebuild_grid(self._rows, self._cols_no_b + 1)
        for i in range(filas):
            for j in range(columnas):
                self._entries[i][j].setText(str(M[i][j]))

    def _parse_equations_text(self, text: str, num_vars_expected: int):
        import fractions as _fra
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            raise ValueError("No hay líneas.")
        var_names = []
        var_indexed = False
        term_re = re.compile(r'([+-]?\s*(?:\d+(?:/\d+)?|\d*\.\d+)?)([a-zA-Z]\w*)')
        const_re = re.compile(r'([+-]?\s*(?:\d+(?:/\d+)?|\d*\.\d+))')
        parsed = []
        for ln in lines:
            if '=' not in ln:
                raise ValueError(f"Falta '=' en la línea: {ln}")
            left, right = ln.split('=', 1)
            left = left.strip(); right = right.strip()
            terms = term_re.findall(left)
            vars_in_line = [v for (_coef, v) in terms]
            if any(re.match(r'^[a-zA-Z]+\d+$', v) for v in vars_in_line):
                var_indexed = True
            for v in vars_in_line:
                if v not in var_names:
                    var_names.append(v)
            parsed.append((left, right))
        if var_indexed:
            mapping = {}
            for name in var_names:
                m = re.match(r'^([a-zA-Z]+)(\d+)$', name)
                if m:
                    idx = int(m.group(2)) - 1
                    mapping[name] = idx
            for i in range(num_vars_expected):
                key = f'x{i+1}'
                if key not in mapping:
                    mapping[key] = i
        else:
            encountered = []
            for ln in lines:
                for m in term_re.finditer(ln.split('=')[0]):
                    name = m.group(2)
                    if name not in encountered:
                        encountered.append(name)
            if len(encountered) < num_vars_expected:
                for i in range(num_vars_expected):
                    key = f'x{i+1}'
                    if key not in encountered:
                        encountered.append(key)
            mapping = {name: idx for idx, name in enumerate(encountered[:num_vars_expected])}
        M = []
        for left, right in parsed:
            coeffs = [ _fra.Fraction(0) for _ in range(num_vars_expected) ]
            for m in term_re.finditer(left):
                raw_coef = m.group(1).replace(' ', '')
                var = m.group(2)
                if raw_coef in ('', '+'):
                    coef = _fra.Fraction(1)
                elif raw_coef == '-':
                    coef = _fra.Fraction(-1)
                else:
                    coef = _fra.Fraction(raw_coef)
                idx = mapping.get(var, None)
                if idx is None or idx < 0 or idx >= num_vars_expected:
                    raise ValueError(f"Variable inesperada '{var}' en la ecuación: {left}={right}")
                coeffs[idx] += coef
            left_consts = 0
            cleaned = term_re.sub(' ', left)
            for m in const_re.finditer(cleaned):
                s = m.group(1).replace(' ', '')
                try:
                    left_consts += _fra.Fraction(s)
                except Exception:
                    pass
            try:
                rhs = _fra.Fraction(right.replace(',', '.'))
            except Exception:
                raise ValueError(f"Constante derecha inválida: '{right}'")
            rhs = rhs - left_consts
            row = coeffs + [rhs]
            M.append(row)
        if len(M) != num_vars_expected:
            raise ValueError(f"Se esperaban {num_vars_expected} ecuaciones (filas) según la dimensión, pero se han dado {len(M)}.")
        return M

    def _leer_matriz(self):
        if not self._entries:
            raise ValueError("Primero cree la matriz.")
        A = []
        for row in self._entries:
            vals = []
            for e in row:
                s = (e.text() or "0").strip()
                vals.append(Fraction(s.replace(",", ".")))
            A.append(vals)
        return A

    def _preview_sistema(self):
        # Construye y muestra el sistema mientras se ingresa la matriz
        try:
            A_aug = self._leer_matriz()
        except Exception:
            A_aug = []
        if not A_aug:
            try:
                self.procedimiento.clear()
            except Exception:
                pass
            return
        try:
            n = len(A_aug); m = len(A_aug[0]); num_vars = max(0, m-1)
            def coef_term(c, j):
                if c == 0: return None
                var = f"x{j+1}"
                if c == 1: return var
                if c == -1: return f"- {var}"
                return f"{_fmt_fraction(c)}{var}"
            lines = []
            for i in range(n):
                parts = []
                for j in range(num_vars):
                    t = coef_term(A_aug[i][j], j)
                    if t is None: continue
                    if not parts:
                        parts.append(str(t))
                    else:
                        tt = str(t)
                        if tt.startswith("-"):
                            clean = tt[2:] if tt.startswith("- ") else tt[1:]
                            parts.append(f"- {clean}")
                        else:
                            parts.append(f"+ {tt}")
                left = " ".join(parts) if parts else "0"
                right = _fmt_fraction(A_aug[i][-1]) if m>0 else "0"
                lines.append(f"{left} = {right}")
            mono_pre = scaled_font_px(13)
            html = (
                "<div style='font-family:Segoe UI;'>"
                "<div style='font-weight:700;margin-bottom:4px;'>Sistema de ecuaciones ingresado:</div>"
                f"<pre style='font-family:Consolas,monospace;font-size:{mono_pre}px;margin:0;'>"
                + "\n".join(lines)
                + "</pre></div>"
            )
            try:
                self.procedimiento.setHtml(html)
            except Exception:
                self.procedimiento.setPlainText("Sistema de ecuaciones ingresado:\n" + "\n".join(lines))
        except Exception:
            pass

    def _toggle_detalles(self):
        # kept for backward compatibility but not used; prefer popup
        visible = self.detalles_container.isVisible()
        self.detalles_container.setVisible(not visible)
        self.toggle_det_btn.setText("Ocultar cálculos de determinantes" if not visible else "Mostrar cálculos de determinantes")

    def _open_detalles_window(self):
        # open a dedicated window with paginated determinante steps
        items = getattr(self, "_det_steps_items", None)
        if not items:
            QMessageBox.information(self, "Sin cálculos", "Primero resuelve el sistema para generar los cálculos de determinantes.")
            return
        w = DetallesDeterminantesWindow(parent=self, items=items)
        w.resize(820, 620)
        w.show()
        self._detalles_window = w

    def _open_settings(self):
        open_settings_dialog(self)

    def _resolver(self):
        try:
            A_aug = self._leer_matriz()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Entrada inválida: {exc}")
            return
        n = len(A_aug)
        if n == 0:
            QMessageBox.warning(self, "Error", "Matriz vacía.")
            return
        m = len(A_aug[0])
        if m != n + 1:
            QMessageBox.warning(self, "Dimensiones incompatibles", "Para Cramer se requiere una matriz aumentada n x (n+1). Ajusta filas/columnas.")
            return

        # separar A y b
        A = [[A_aug[i][j] for j in range(m - 1)] for i in range(n)]
        b = [A_aug[i][-1] for i in range(n)]

        # calculo de det(A)
        detA, pasosA = determinante_con_pasos_ascii(A)
        # mostrar detA distintivo
        self.det_label.setText(f"det(A) = {_fmt_fraction(detA)}")

        if detA == 0:
            # mostrar mensaje y detallar pasos en la sección de determinantes
            QMessageBox.critical(self, "No se puede aplicar Cramer", "El determinante de la matriz de coeficientes es cero. No se puede resolver por el método de Cramer.")
        # calcular determinantes para cada variable
        det_vars = []
        det_steps = {"detA": pasosA}
        for col in range(n):
            # construir matriz con columna col reemplazada por b
            M = [row[:] for row in A]
            for i in range(n):
                M[i][col] = b[i]
            detk, pasosk = determinante_con_pasos_ascii(M)
            det_vars.append(detk)
            det_steps[f"det_var_{col+1}"] = pasosk

        # preparar items paginados para la ventana de detalles: lista de (titulo, lineas)
        self._det_steps_items = []
        # primer item: det(A)
        self._det_steps_items.append(("|A| — determinante general", pasosA))
        for idx in range(n):
            key = f"det_var_{idx+1}"
            lines = det_steps.get(key, [])
            self._det_steps_items.append((f"|A{idx+1}| — determinante sustituyendo columna {idx+1}", lines))

        # preparar y mostrar resultados
        self.vars_box.clear()
        if detA != 0:
            lines = []
            for i, detk in enumerate(det_vars):
                val = detk / detA
                lines.append(f"x{i+1} = {_fmt_fraction(detk)} / {_fmt_fraction(detA)} = {_fmt_fraction(val)}")
            self.vars_box.setPlainText("\n".join(lines))
        else:
            # si detA == 0 ofrecer interpretación: mostrar det vars si se desea
            self.vars_box.setPlainText("Determinante cero: no aplicable. Se muestran los determinantes sustituidos si los desea ver.")

        # procedimiento principal (alto nivel) — ahora formateado en HTML + <pre>
        mono_small = scaled_font_px(13)
        mono_large = scaled_font_px(15)
        formula_font = scaled_font_px(14)
        # Queremos: 1) Regla de Cramer (fórmula). 2) Con valores: mostrar |A|, |A1|, |A2|... con matrices dentro de barras
        def _matrix_block_html(M):
            # devuelve HTML con <pre> que representa la matriz entre barras
            # calcular ancho por columna
            if not M:
                return "<pre> | | </pre>"
            rows = [[_fmt_fraction(x) for x in r] for r in M]
            cols = len(rows[0])
            widths = [0] * cols
            for r in rows:
                for j, cell in enumerate(r):
                    widths[j] = max(widths[j], len(cell))
            lines = []
            for r in rows:
                cells = [str(r[j]).rjust(widths[j]) for j in range(cols)]
                lines.append("  | " + "  ".join(cells) + " |")
            return (
                f"<pre style='font-family:Consolas,monospace;font-size:{mono_small}px; margin:6px;'>"
                + "\n".join(lines)
                + "</pre>"
            )

        def _matrix_block_html_aug(M, bvec):
            # Representación de matriz aumentada A | b con separador vertical antes de la última columna
            if not M:
                return "<pre> | | </pre>"
            rows = []
            # A columns
            a_rows = [[_fmt_fraction(x) for x in r] for r in M]
            b_cells = [_fmt_fraction(x) for x in bvec]
            colsA = len(a_rows[0])
            widths = [0] * colsA
            width_b = 0
            for r in a_rows:
                for j, cell in enumerate(r):
                    widths[j] = max(widths[j], len(cell))
            for cell in b_cells:
                width_b = max(width_b, len(cell))

            lines = []
            for i, r in enumerate(a_rows):
                cells = [r[j].rjust(widths[j]) for j in range(colsA)]
                bcell = b_cells[i].rjust(width_b)
                # use a visible separator ' | ' between A and b
                lines.append("  | " + "  ".join(cells) + "  | " + bcell + " |")
            return (
                f"<pre style='font-family:Consolas,monospace;font-size:{mono_small}px; margin:6px;'>"
                + "\n".join(lines)
                + "</pre>"
            )

        # Cabecera con la fórmula
        html_parts = []
        html_parts.append("<div style='text-align:center; font-family:Segoe UI, sans-serif;'>")
        # Sistema de ecuaciones ingresado (desde A y b)
        try:
            def _eq_lines(Aeq, beq):
                nloc = len(Aeq)
                mloc = len(Aeq[0]) if nloc else 0
                out = []
                for i in range(nloc):
                    parts = []
                    for j in range(mloc):
                        c = Aeq[i][j]
                        if c == 0:
                            continue
                        var = f"x{j+1}"
                        if c == 1:
                            term = var
                        elif c == -1:
                            term = f"- {var}"
                        else:
                            term = f"{_fmt_fraction(c)}{var}"
                        if not parts:
                            parts.append(term)
                        else:
                            if term.startswith("-"):
                                clean = term[2:] if term.startswith("- ") else term[1:]
                                parts.append(f"- {clean}")
                            else:
                                parts.append(f"+ {term}")
                    left = " ".join(parts) if parts else "0"
                    right = _fmt_fraction(beq[i]) if i < len(beq) else "0"
                    out.append(f"{left} = {right}")
                return out
            eq_block = (
                "<div style='text-align:left; display:inline-block; margin:8px 0;'>"
                "<div style='font-weight:700; margin-bottom:4px;'>Sistema de ecuaciones ingresado:</div>"
                f"<pre style='font-family:Consolas,monospace;font-size:{mono_small}px;margin:0;'>"
                + "\n".join(_eq_lines(A, b))
                + "</pre></div>"
            )
            html_parts.append(eq_block)
        except Exception:
            pass
        html_parts.append("<h3 style='margin:6px 0;'>Regla de Cramer (fórmula):</h3>")
        html_parts.append(
            f"<div style='font-size:{formula_font}px; margin-bottom:10px;'>Para i = 1, ..., n: <b>x<sub>i</sub> = |A<sub>i</sub>| / |A|</b></div>"
        )

        # Mostrar primero la matriz aumentada centrada (A | b)
        html_parts.append("<div style='width:100%; text-align:center; margin-bottom:6px;'>")
        html_parts.append("<div style='display:inline-block; text-align:center;'>")
        html_parts.append("<div style='text-align:center; font-weight:700; margin-bottom:6px;'>Matriz aumentada (A | b)</div>")
        html_parts.append(_matrix_block_html_aug(A, b))
        html_parts.append("</div>")
        html_parts.append("</div>")

        # luego mostrar la matriz A sola (centrada)
        html_parts.append("<div style='width:100%; text-align:center; margin-bottom:6px;'>")
        html_parts.append("<div style='display:inline-block; text-align:center;'>")
        html_parts.append("<div style='text-align:center; font-weight:700; margin-bottom:6px;'>Matriz A (coeficientes)</div>")
        html_parts.append(_matrix_block_html(A))
        html_parts.append("</div>")
        html_parts.append("</div>")

        # Mostrar los determinantes con matrices (sin expandir)
        html_parts.append("<div style='clear:both; margin-top:12px; text-align:center;'>")
        html_parts.append("<div style='font-weight:700; margin-bottom:6px;'>Con valores:</div>")
        # det(A)
        html_parts.append("<div style='display:inline-block; margin:6px 18px; text-align:center;'>")
        html_parts.append("<div style='font-weight:600'>&#124;A&#124; =</div>")
        html_parts.append(_matrix_block_html(A))
        html_parts.append(f"<div style='margin-top:6px; font-weight:700;'>= {_fmt_fraction(detA)}</div>")
        html_parts.append("</div>")

        # cada det Ai
        for idx in range(n):
            # construir Ai
            M = [row[:] for row in A]
            for i in range(n):
                M[i][idx] = b[i]
            html_parts.append("<div style='display:inline-block; margin:6px 18px; text-align:center;'>")
            html_parts.append(f"<div style='font-weight:600'>&#124;A<sub>{idx+1}</sub>&#124; =</div>")
            html_parts.append(_matrix_block_html(M))
            html_parts.append(f"<div style='margin-top:6px; font-weight:700;'>= {_fmt_fraction(det_vars[idx])}</div>")
            html_parts.append("</div>")

        html_parts.append("</div>")

        # finalmente mostrar solución compacta (con formato completo: det/ det = valor)
        html_parts.append("<div style='margin-top:12px; text-align:center; font-weight:700;'>Solución:</div>")
        sol_html_lines = []
        if detA == 0:
            sol_html_lines.append("det(A) = 0 → El método de Cramer no es aplicable.")
        else:
            for i, detk in enumerate(det_vars):
                val = detk / detA
                # formatear como: x1 = |A1|/|A| = 24/-12 = -2
                left = f"x{i+1} = "
                frac = f"|A{i+1}| / |A| = {_fmt_fraction(detk)} / {_fmt_fraction(detA)} = {_fmt_fraction(val)}"
                sol_html_lines.append(left + frac)
        # usar <pre> para mantener alineación y un recuadro un poco más grande
        html_parts.append(
            f"<pre style='font-family:Consolas,monospace; font-size:{mono_large}px; text-align:left; display:inline-block; padding:12px; margin-top:8px; border:1px solid #ddd; border-radius:6px; background:#fff;'>"
        )
        html_parts.append("\n".join(sol_html_lines))
        html_parts.append("</pre>")

        html_parts.append("</div>")
        proc_html = "\n".join(html_parts)
        try:
            # aumentar ligeramente el tamaño visible del QTextEdit para el procedimiento
            self.procedimiento.setMinimumHeight(340)
            self.procedimiento.setHtml(proc_html)
        except Exception:
            # fallback a texto simple
            self.procedimiento.setPlainText("Regla de Cramer:\n" + "\n".join(sol_html_lines))

        # rellenar detalles de cálculos de determinantes (no visible por defecto)
        detalles_text = []
        detalles_text.append("Cálculos detallados de determinantes:\n")
        detalles_text.append("-- det(A) --")
        detalles_text.extend(pasosA)
        detalles_text.append("\n")
        for idx in range(n):
            detalles_text.append(f"-- det sustituyendo columna x{idx+1} --")
            detalles_text.extend(det_steps[f"det_var_{idx+1}"])
            detalles_text.append("\n")

        self.detalles_text.setPlainText("\n".join(detalles_text))
