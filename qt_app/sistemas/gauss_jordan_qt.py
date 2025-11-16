from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QLineEdit, QTextEdit, QMessageBox, QFrame,
    QDialog, QDialogButtonBox, QPlainTextEdit, QSlider, QToolButton, QMenu
)
from PySide6.QtCore import Qt, QSize
from fractions import Fraction
from copy import deepcopy
import re
from ..theme import bind_font_scale_stylesheet, bind_theme_icon, make_overflow_icon, gear_icon_preferred
from ..settings_qt import open_settings_dialog


def _fmt(x):
    try:
        return str(x)
    except Exception:
        return f"{x}"


class GaussJordanWindow(QMainWindow):
    def __init__(self, parent=None, start_with_independencia=False):
        super().__init__(parent)
        self.setWindowTitle("Método de Eliminación de Gauss-Jordan")
        self._entries = []
        self._rows = 3
        self._cols_no_b = 3
        self.pasos_guardados = []
        self.matriz_final = None
        self.matriz_original = None
        self.detalle_button = None
        self.mostrando_detalles = False

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
        # sin tama�o fijo
        more_btn.setAutoRaise(True)
        more_btn.setCursor(Qt.PointingHandCursor)
        more_btn.setToolTip("M�s opciones")
        more_btn.setPopupMode(QToolButton.InstantPopup)
        try:
            from PySide6.QtCore import QSize
            from ..theme import bind_theme_icon, make_overflow_icon, gear_icon_preferred
            bind_theme_icon(more_btn, make_overflow_icon, 20)
            more_btn.setIconSize(QSize(20, 20))
        except Exception:
            pass
        menu = QMenu(more_btn)
        try:
            act_settings = menu.addAction(gear_icon_preferred(22), "Configuraci�n")
        except Exception:
            act_settings = menu.addAction("Configuraci�n")
        act_settings.triggered.connect(self._open_settings)
        more_btn.setMenu(menu)
        top.addWidget(more_btn)
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
        self.result = QTextEdit()
        self.result.setReadOnly(True)
        bind_font_scale_stylesheet(
            self.result,
            "font-family: Consolas, monospace; font-size: {body}px;",
            body=12,
        )
        main.addWidget(self.result, 1)

        self.btn_resolver = QPushButton("Resolver")
        self.btn_resolver.clicked.connect(self._resolver)
        self.btn_resolver.setEnabled(False)
        main.addWidget(self.btn_resolver)

        bottom = QHBoxLayout()
        main.addLayout(bottom)
        bottom.addStretch(1)
        self.detalle_button = QPushButton("Ver pasos detallados")
        self.detalle_button.setEnabled(False)
        self.detalle_button.clicked.connect(self._toggle_detalles)
        bottom.addWidget(self.detalle_button)

        self._rebuild_grid(self._rows, self._cols_no_b + 1)

    def _limpiar(self):
        self._entries = []
        while self.grid_layout.count():
            w = self.grid_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.result.clear()
        self.btn_resolver.setEnabled(False)
        # Resetear estado para permitir vista previa y nuevas resoluciones
        self.pasos_guardados = []
        self.matriz_final = None
        self.matriz_original = None
        self.mostrando_detalles = False
        try:
            if self.detalle_button:
                self.detalle_button.setEnabled(False)
        except Exception:
            pass

    def _rebuild_grid(self, filas: int, columnas: int):
        old = [[e.text() for e in row] for row in self._entries] if self._entries else []
        self._limpiar()
        for j in range(columnas - 1):
            h = QLabel(f"x{j+1}")
            h.setStyleSheet("font-weight: 700;")
            self.grid_layout.addWidget(h, 0, j)
        hb = QLabel("b")
        hb.setStyleSheet("font-weight: 700;")
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

    # --- ingreso por ecuaciones (nuevo): abrir diálogo y parsear ---
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
        # aplicar la matriz aumentada a la cuadrícula (ajustar tamaño)
        filas = len(M)
        columnas = len(M[0]) if filas else 0
        if filas == 0:
            QMessageBox.warning(self, "Error", "No se detectaron ecuaciones válidas.")
            return
        # reconstruir y llenar
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
                val = M[i][j]
                self._entries[i][j].setText(str(val))

    def _open_settings(self):
        open_settings_dialog(self)

    def _parse_equations_text(self, text: str, num_vars_expected: int):
        """Parsea texto con una ecuación por línea y devuelve matriz aumentada de Fraction.
        num_vars_expected es el número de variables (n). Se requieren exactamente n ecuaciones.
        """
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            raise ValueError("No hay líneas.")
        # intentaremos inferir variables: si aparecen x1,x2.. usamos índices; sino recolectamos letras en orden
        var_names = []
        var_indexed = False
        term_re = re.compile(r'([+-]?\s*(?:\d+(?:/\d+)?|\d*\.\d+)?)([a-zA-Z]\w*)')
        const_re = re.compile(r'([+-]?\s*(?:\d+(?:/\d+)?|\d*\.\d+))')
        parsed = []
        for ln in lines:
            if '=' not in ln:
                raise ValueError(f"Falta '=' en la línea: {ln}")
            left, right = ln.split('=', 1)
            left = left.strip()
            right = right.strip()
            # encontrar términos con variables
            terms = term_re.findall(left)
            vars_in_line = [v for (_coef, v) in terms]
            if any(re.match(r'^[a-zA-Z]+\d+$', v) for v in vars_in_line):
                var_indexed = True
            for v in vars_in_line:
                if v not in var_names:
                    var_names.append(v)
            parsed.append((left, right))

        # construir mapa de variables según num_vars_expected
        if var_indexed:
            # variables like x1,x2 -> map by trailing digits
            mapping = {}
            for name in var_names:
                m = re.match(r'^([a-zA-Z]+)(\d+)$', name)
                if m:
                    idx = int(m.group(2)) - 1
                    mapping[name] = idx
            # ensure mapping covers 0..n-1
            # if not, generate generic names x1..xn
            for i in range(num_vars_expected):
                key = f'x{i+1}'
                if key not in mapping:
                    mapping[key] = i
        else:
            # pick first distinct variable letters up to num_vars_expected
            encountered = []
            for ln in lines:
                for m in term_re.finditer(ln.split('=')[0]):
                    name = m.group(2)
                    if name not in encountered:
                        encountered.append(name)
            if len(encountered) < num_vars_expected:
                # pad with x1..xn
                for i in range(num_vars_expected):
                    key = f'x{i+1}'
                    if key not in encountered:
                        encountered.append(key)
            mapping = {name: idx for idx, name in enumerate(encountered[:num_vars_expected])}

        # ahora parsear cada línea y construir coeficientes
        from fractions import Fraction as _F
        M = []
        for left, right in parsed:
            coeffs = [ _F(0) for _ in range(num_vars_expected) ]
            # sacar constantes sueltos en left (números sin variable)
            # extraer variable terms
            for m in term_re.finditer(left):
                raw_coef = m.group(1).replace(' ', '')
                var = m.group(2)
                if raw_coef in ('', '+'):
                    coef = _F(1)
                elif raw_coef == '-':
                    coef = _F(-1)
                else:
                    coef = _F(raw_coef)
                idx = mapping.get(var, None)
                if idx is None or idx < 0 or idx >= num_vars_expected:
                    raise ValueError(f"Variable inesperada '{var}' en la ecuación: {left}={right}")
                coeffs[idx] += coef
            # constantes on left (numbers without variable): move to right
            left_consts = 0
            # remove variable terms to find standalone numbers
            cleaned = term_re.sub(' ', left)
            for m in const_re.finditer(cleaned):
                s = m.group(1).replace(' ', '')
                try:
                    left_consts += _F(s)
                except Exception:
                    pass
            try:
                rhs = _F(right.replace(',', '.'))
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
                vals.append(Fraction(s))
            A.append(vals)
        return A

    def _equations_from_aug(self, A_aug):
        if not A_aug:
            return []
        n = len(A_aug)
        m = len(A_aug[0])
        num_vars = max(0, m - 1)

        def coef_term(c, j):
            if c == 0:
                return None
            var = f"x{j+1}"
            if c == 1:
                return f"{var}"
            if c == -1:
                return f"- {var}"
            return f"{c}{var}"

        lines = []
        for i in range(n):
            parts = []
            for j in range(num_vars):
                t = coef_term(A_aug[i][j], j)
                if t is None:
                    continue
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
            right = str(A_aug[i][-1]) if m > 0 else "0"
            lines.append(f"{left} = {right}")
        return lines

    def _preview_sistema(self):
        # No sobreescribir resultados si ya se resolvi
        if self.matriz_final is not None:
            return
        try:
            A = []
            for row in self._entries:
                vals = []
                for e in row:
                    s = (e.text() or "0").strip()
                    vals.append(Fraction(s))
                A.append(vals)
            lines = self._equations_from_aug(A)
        except Exception:
            lines = []
        try:
            self.result.clear()
            if lines:
                self.result.insertPlainText("Sistema de ecuaciones ingresado:\n")
                for ln in lines:
                    self.result.insertPlainText(ln + "\n")
        except Exception:
            pass

    def _equations_from_aug(self, A_aug):
        if not A_aug:
            return []
        n = len(A_aug)
        m = len(A_aug[0])
        num_vars = max(0, m - 1)

        def coef_term(c, j):
            if c == 0:
                return None
            var = f"x{j+1}"
            if c == 1:
                return f"{var}"
            if c == -1:
                return f"- {var}"
            return f"{c}{var}"

        lines = []
        for i in range(n):
            parts = []
            for j in range(num_vars):
                t = coef_term(A_aug[i][j], j)
                if t is None:
                    continue
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
            right = str(A_aug[i][-1]) if m > 0 else "0"
            lines.append(f"{left} = {right}")
        return lines

    def _resolver(self):
        try:
            A = self._leer_matriz()
            filas = len(A)
            cols = len(A[0])
            self.matriz_original = deepcopy(A)
            pasos = gauss_jordan(A, filas, cols)
            self.pasos_guardados = pasos
            self.matriz_final = A
            self._mostrar_resumen()
            self.detalle_button.setEnabled(True)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Entrada inválida: {exc}")

    def _insert_header(self, titulo: str, comentario: str = ""):
        self.result.insertPlainText("Operación: ")
        self.result.insertPlainText(titulo)
        if comentario:
            self.result.insertPlainText("  \u2014  ")
            self.result.insertPlainText(comentario)
        self.result.insertPlainText("\n\n")

    def _mostrar_detalles(self):
        self.result.clear()
        for step in self.pasos_guardados:
            self._insert_header(step.get("titulo", ""), step.get("comentario", ""))
            oper_lines = step.get("oper_lines", [])
            matriz_lines = step.get("matriz_lines", [])
            max_left = max((len(s) for s in oper_lines), default=0)
            sep = "   |   "
            max_len = max(len(oper_lines), len(matriz_lines))
            for i in range(max_len):
                left = oper_lines[i] if i < len(oper_lines) else ""
                right = matriz_lines[i] if i < len(matriz_lines) else ""
                line_text = left.ljust(max_left) + (sep if right else "") + right
                self.result.insertPlainText(line_text + "\n")
            self.result.insertPlainText("\n" + ("-" * 110) + "\n\n")
        self.result.insertPlainText("===== SOLUCIÓN FINAL =====\n")
        soluciones, tipo, _ = _extraer_soluciones(self.matriz_final)
        for i, val in enumerate(soluciones):
            self.result.insertPlainText(f"x{i+1} = {val}\n")

    def _mostrar_resumen(self):
        self.result.clear()
        self.result.insertPlainText("===== SOLUCIÓN FINAL =====\n")
        if self.matriz_final is None:
            self.result.insertPlainText("(no hay soluciones calculadas)\n")
            return
        soluciones, tipo, analisis = _extraer_soluciones(self.matriz_final)
        if tipo == "incompatible":
            self.result.insertPlainText("El sistema es inconsistente: aparece una fila del tipo 0 = b con b≠0\n")
            return
        if tipo == "determinado":
            self.result.insertPlainText("El sistema tiene solución única:\n\n")
        elif tipo == "indeterminado":
            self.result.insertPlainText("El sistema tiene infinitas soluciones:\n\n")
        for i, val in enumerate(soluciones):
            self.result.insertPlainText(f"x{i+1} = {val}\n")

        # Forma vectorial estilo libro cuando hay variables libres
        if tipo == "indeterminado":
            pivot_cols, free_cols, pivot_row_for_col = analisis
            if free_cols:
                self.result.insertPlainText("\nConjunto solución:\n\n")
                num_vars = len(soluciones)
                # Vector particular (libres = 0)
                particular = []
                for j in range(num_vars):
                    if j in free_cols:
                        particular.append(Fraction(0))
                    else:
                        irow = pivot_row_for_col.get(j, None)
                        particular.append(self.matriz_final[irow][-1] if irow is not None else Fraction(0))
                # Vectores base de cada libre
                vectores_libres = []
                for l in free_cols:
                    v = [Fraction(0)] * num_vars
                    v[l] = Fraction(1)
                    for j in pivot_cols:
                        irow = pivot_row_for_col[j]
                        v[j] = -self.matriz_final[irow][l]
                    vectores_libres.append(v)

                es_homogeneo = all(self.matriz_original[i][-1] == 0 for i in range(len(self.matriz_original))) if self.matriz_original else False
                if not es_homogeneo:
                    nombres = ["  "] + [f"x{l+1}" for l in free_cols]
                    vectores = [particular] + vectores_libres
                else:
                    nombres = [f"x{l+1}" for l in free_cols]
                    vectores = vectores_libres

                lines = vectores_columna_lado_a_lado(vectores, nombres, espacio_entre_vectores=4)
                imprimir_vectores_con_x_igual(self.result, lines)
                self.result.insertPlainText("\nDonde " + ", ".join([f"x{l+1}" for l in free_cols]) + " ∈ ℝ (parámetros libres).\n")

    def _toggle_detalles(self):
        if not self.pasos_guardados:
            return
        if self.mostrando_detalles:
            self._mostrar_resumen()
            self.detalle_button.setText("Ver pasos detallados")
            self.mostrando_detalles = False
        else:
            self._mostrar_detalles()
            self.detalle_button.setText("Ocultar pasos detallados")
            self.mostrando_detalles = True

    # _verificar_independencia retirado a petición del usuario

    def _go_back(self):
        try:
            p = self.parent()
            self.close()
            if p is not None:
                p.show()
                p.activateWindow()
        except Exception:
            self.close()


def gauss_jordan(A, n, m):
    pasos = []
    fila_pivote = 0
    for col in range(m - 1):
        pivote = None
        for f in range(fila_pivote, n):
            if A[f][col] != 0:
                pivote = f
                break
        if pivote is None:
            continue
        if pivote != fila_pivote:
            A[fila_pivote], A[pivote] = A[pivote], A[fila_pivote]
            pasos.append({
                "titulo": f"F{fila_pivote+1} \u2194 F{pivote+1}",
                "comentario": f"Intercambio de filas para poner un pivote no nulo en la columna {col+1}",
                "oper_lines": [],
                "matriz_lines": format_matriz_lines(A)
            })
        divisor = A[fila_pivote][col]
        if divisor == 0:
            fila_pivote += 1
            continue
        if divisor != 1:
            A[fila_pivote] = [val / divisor for val in A[fila_pivote]]
            pasos.append({
                "titulo": f"F{fila_pivote+1} \u2192 F{fila_pivote+1}/{_fmt(divisor)}",
                "comentario": f"Normalización: se convierte en pivote a 1 en la columna {col+1}",
                "oper_lines": [],
                "matriz_lines": format_matriz_lines(A)
            })
        for f in range(n):
            if f != fila_pivote and A[f][col] != 0:
                factor = A[f][col]
                original_fila = A[f][:]
                A[f] = [original_fila[j] - factor * A[fila_pivote][j] for j in range(m)]
                oper_lines = format_operacion_vertical_lines(
                    A[fila_pivote], original_fila, factor, A[f], fila_pivote + 1, f + 1
                )
                pasos.append({
                    "titulo": f"F{f+1} \u2192 F{f+1} - ({_fmt(factor)})F{fila_pivote+1}",
                    "comentario": f"Se anula el elemento en la columna {col+1} usando la fila pivote",
                    "oper_lines": oper_lines,
                    "matriz_lines": format_matriz_lines(A)
                })
        fila_pivote += 1
        if fila_pivote >= n:
            break
    return pasos


def format_operacion_vertical_lines(fila_pivote, fila_actual, factor, fila_result, idx_piv, idx_obj):
    ancho = max(len(str(x)) for x in fila_result) if fila_result else 1

    def fmt(lst):
        return " ".join(str(x).rjust(ancho) for x in lst)

    escala = [(-factor) * val for val in fila_pivote]

    if factor < 0:
        factor_str = f"+{abs(factor)}"
    else:
        factor_str = f"-{factor}"

    lines = [
        f"{factor_str}F{idx_piv} : {fmt(escala)}",
        f"+F{idx_obj}   : {fmt(fila_actual)}",
        " " * 10 + "-" * (ancho * len(fila_result) + len(fila_result) - 1),
        f"=F{idx_obj}   : {fmt(fila_result)}"
    ]
    return lines


def format_matriz_lines(A):
    ancho = 1
    for fila in A:
        for x in fila:
            ancho = max(ancho, len(str(x)))
    lines = []
    for fila in A:
        line = " ".join(str(x).rjust(ancho) for x in fila)
        lines.append(line)
    return lines


# Helpers para análisis de RREF y forma vectorial
def _analizar_rref(A):
    n = len(A); m = len(A[0]); num_vars = m - 1
    piv_col_por_fila = [-1] * n
    piv_fila_por_col = {}
    for i in range(n):
        for j in range(num_vars):
            if A[i][j] == 1 and all(A[k][j] == 0 for k in range(n) if k != i):
                piv_col_por_fila[i] = j
                piv_fila_por_col[j] = i
                break
    pivot_cols = [j for j in piv_col_por_fila if j != -1]
    free_cols = [j for j in range(num_vars) if j not in pivot_cols]
    return pivot_cols, free_cols, piv_fila_por_col


def _extraer_soluciones(A):
    n = len(A); m = len(A[0]); num_vars = m - 1
    # Incompatibilidad: [0 ... 0 | b≠0]
    for i in range(n):
        if all(A[i][j] == 0 for j in range(num_vars)) and A[i][-1] != 0:
            return None, "incompatible", ([], [], {})
    pivot_cols, free_cols, pivot_row_for_col = _analizar_rref(A)
    soluciones = [None] * num_vars
    if free_cols:
        for j in range(num_vars):
            if j in free_cols:
                soluciones[j] = f"x{j+1} es variable libre"
            else:
                irow = pivot_row_for_col.get(j, None)
                partes = []
                if irow is not None and A[irow][-1] != 0:
                    partes.append(str(A[irow][-1]))
                for l in free_cols:
                    if irow is not None:
                        coef = -A[irow][l]
                        if coef != 0:
                            partes.append(f"({coef})*x{l+1}")
                expr = " + ".join(partes) if partes else "0"
                soluciones[j] = expr
        return soluciones, "indeterminado", (pivot_cols, free_cols, pivot_row_for_col)
    else:
        # Determinado
        for j in range(num_vars):
            irow = pivot_row_for_col.get(j, None)
            soluciones[j] = A[irow][-1] if irow is not None else 0
        return soluciones, "determinado", (pivot_cols, free_cols, pivot_row_for_col)


def vectores_columna_lado_a_lado(vectores, nombres, espacio_entre_vectores=4):
    n = len(vectores[0]) if vectores else 0
    m = len(vectores)
    encabezados = [nombres[0]] + [f"+ {nombres[idx]}" for idx in range(1, m)]
    max_encabezado = max((len(e) for e in encabezados), default=0)
    max_num_len = 1
    for v in vectores:
        for fila in range(n):
            max_num_len = max(max_num_len, len(str(v[fila])))
    bloque_ancho = max_encabezado + 3 + max_num_len + 2
    sep = " " * espacio_entre_vectores
    lines = []
    for fila in range(n):
        line = ""
        for idx, v in enumerate(vectores):
            valstr = str(v[fila]).rjust(max_num_len)
            if fila == 0:
                li, ri = "\u23A1", "\u23A4"  # ⎡ ⎤
            elif fila == n - 1:
                li, ri = "\u23A3", "\u23A6"  # ⎣ ⎦
            else:
                li, ri = "\u23A2", "\u23A5"  # ⎢ ⎥
            if fila == 0:
                encabezado = encabezados[idx].rjust(max_encabezado)
                bloque = f"{encabezado} {li} {valstr} {ri}"
            else:
                bloque = " " * max_encabezado + f" {li} {valstr} {ri}"
            bloque = bloque.ljust(bloque_ancho)
            if idx < m - 1:
                bloque += sep
            line += bloque
        lines.append(line.rstrip())
    return lines


def imprimir_vectores_con_x_igual(editor: QTextEdit, lines):
    if not lines:
        return
    x_eq = "x ="
    first = lines[0]
    pos = first.find("\u23A1")
    pos = 0 if pos < 0 else pos
    x_pos = max(0, pos - len(x_eq) - 1)
    for i, l in enumerate(lines):
        if i == 0:
            editor.insertPlainText(" " * x_pos + x_eq + " " + l + "\n")
        else:
            editor.insertPlainText(" " * (x_pos + len(x_eq) + 1) + l + "\n")

