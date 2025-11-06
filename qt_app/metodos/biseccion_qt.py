from math import isfinite
import math
from dataclasses import dataclass
from typing import Callable, List, Tuple

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QLineEdit,
    QScrollArea,
    QGridLayout,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QSpinBox,
    QSizePolicy,
    QHeaderView,
    QDialog,
    QDialogButtonBox,
    QToolButton,
    QMenu,
)
from PySide6.QtCore import Qt

from ..theme import (
    bind_font_scale_stylesheet,
    install_toggle_shortcut,
    bind_theme_icon,
    make_overflow_icon,
    gear_icon_preferred,
)
from ..settings_qt import open_settings_dialog

# Import plotting libraries when needed. We'll import lazily inside the plotting method


_ALLOWED_NAMES = {
    name: getattr(math, name)
    for name in dir(math)
    if not name.startswith("_")
}
_ALLOWED_NAMES.update(
    {
        "abs": abs,
        "pow": pow,
        "pi": math.pi,
        "e": math.e,
    }
)


def _format_number(value: float) -> str:
    try:
        if not isfinite(value):
            return str(value)
        value = float(value)
    except Exception:
        return str(value)

    if value == 0.0:
        return "0"
    if abs(value) >= 1_000_000 or abs(value) < 1e-5:
        return f"{value:.6e}"
    text = f"{value:.10f}".rstrip("0").rstrip(".")
    return text or "0"


def _parse_numeric(text: str) -> float:
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Ingrese un número válido.")
    cleaned = cleaned.replace("^", "**")
    # Evitar que el usuario utilice la variable x en intervalos o tolerancia
    if "x" in cleaned.lower():
        raise ValueError("Los parámetros numéricos no deben contener la variable x.")
    try:
        value = eval(cleaned, {"__builtins__": {}}, dict(_ALLOWED_NAMES))
    except Exception as exc:
        raise ValueError(f"No se pudo interpretar el número '{cleaned}': {exc}") from exc
    try:
        return float(value)
    except Exception as exc:
        raise ValueError(f"El valor '{cleaned}' no es numérico.") from exc


def _compile_function(expr: str) -> Callable[[float], float]:
    cleaned = (expr or "").strip()
    if not cleaned:
        raise ValueError("Ingrese una función f(x).")
    cleaned = cleaned.replace("==", "=")
    if "=" in cleaned:
        parts = cleaned.split("=")
        if len(parts) != 2:
            raise ValueError("Solo se admite una igualdad del tipo expresión = 0.")
        left, right = (p.strip() for p in parts)
        if not left or not right:
            raise ValueError("Completa ambos lados de la igualdad, por ejemplo: cos(x) - x = 0.")
        cleaned = f"({left}) - ({right})"
    try:
        code = compile(cleaned, "<función>", "eval")
    except Exception as exc:
        raise ValueError(f"No se pudo compilar la función: {exc}") from exc

    def _fn(x: float) -> float:
        local = dict(_ALLOWED_NAMES)
        local["x"] = x
        value = eval(code, {"__builtins__": {}}, local)
        return float(value)

    # Verificación rápida para detectar errores inmediatos
    try:
        _ = _fn(0.0)
    except Exception:
        # No levantamos, simplemente dejamos que se maneje al evaluar
        pass

    return _fn


@dataclass
class BisectionStep:
    iteration: int
    a: float
    b: float
    c: float
    fa: float
    fb: float
    fc: float


def _run_bisection(
    func: Callable[[float], float],
    a: float,
    b: float,
    tol: float,
    max_iterations: int = 1000,
) -> Tuple[List[BisectionStep], float, float, int]:
    fa = func(a)
    fb = func(b)
    if not (fa * fb < 0):
        raise ValueError("El intervalo inicial debe contener la raíz (f(a) * f(b) < 0).")

    steps: List[BisectionStep] = []
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        c = (a + b) / 2.0
        fc = func(c)
        step = BisectionStep(iteration, a, b, c, fa, fb, fc)
        steps.append(step)

        if abs(fc) < tol:
            return steps, c, fc, iteration

        if fa * fc < 0:
            b = c
            fb = fc
        else:
            a = c
            fa = fc

    raise ValueError("El método excedió el máximo de iteraciones permitidas.")


class RootInputCard(QFrame):
    def __init__(self, index: int):
        super().__init__()
        self.setObjectName("InnerCard")
        self.setStyleSheet(
            """
            QFrame#InnerCard {
                background-color: rgba(255, 255, 255, 0.82);
                border-radius: 16px;
            }
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.title = QLabel()
        self.title.setObjectName("Subtitle")
        layout.addWidget(self.title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(12)
        layout.addLayout(grid)

        lbl_func = QLabel("f(x):")
        lbl_func.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl_func, 0, 0)
        self.function_edit = QLineEdit()
        self.function_edit.setPlaceholderText("Ejemplo: x**3 - x - 2")
        self.function_edit.setClearButtonEnabled(True)
        grid.addWidget(self.function_edit, 0, 1, 1, 2)

        lbl_intervalo = QLabel("Intervalo [a, b]:")
        lbl_intervalo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl_intervalo, 1, 0)

        interval_widget = QWidget()
        interval_layout = QHBoxLayout(interval_widget)
        interval_layout.setContentsMargins(0, 0, 0, 0)
        interval_layout.setSpacing(10)

        lbl_a = QLabel("a =")
        interval_layout.addWidget(lbl_a)

        self.a_edit = QLineEdit()
        self.a_edit.setPlaceholderText("Ejemplo: 1")
        self.a_edit.setAlignment(Qt.AlignCenter)
        self.a_edit.setClearButtonEnabled(True)
        self.a_edit.setToolTip("Extremo izquierdo del intervalo")
        interval_layout.addWidget(self.a_edit)

        lbl_b = QLabel("b =")
        interval_layout.addWidget(lbl_b)

        self.b_edit = QLineEdit()
        self.b_edit.setPlaceholderText("Ejemplo: 2")
        self.b_edit.setAlignment(Qt.AlignCenter)
        self.b_edit.setClearButtonEnabled(True)
        self.b_edit.setToolTip("Extremo derecho del intervalo")
        interval_layout.addWidget(self.b_edit)

        interval_layout.addStretch(1)

        grid.addWidget(interval_widget, 1, 1, 1, 3)

        lbl_tol = QLabel("Tolerancia:")
        lbl_tol.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl_tol, 2, 0)
        self.tol_edit = QLineEdit()
        self.tol_edit.setPlaceholderText("Ejemplo: 0.0001")
        self.tol_edit.setAlignment(Qt.AlignCenter)
        self.tol_edit.setClearButtonEnabled(True)
        grid.addWidget(self.tol_edit, 2, 1, 1, 3)

        lbl_aprox = QLabel("Valor aproximado (opcional):")
        lbl_aprox.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl_aprox, 3, 0)
        self.approx_edit = QLineEdit()
        self.approx_edit.setPlaceholderText("Ejemplo: 1.2")
        self.approx_edit.setAlignment(Qt.AlignCenter)
        self.approx_edit.setClearButtonEnabled(True)
        self.approx_edit.setToolTip("Ingresa un valor esperado para comparar, deja vacío si no aplica.")
        grid.addWidget(self.approx_edit, 3, 1, 1, 3)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)

        bind_font_scale_stylesheet(
            self.title,
            "color:#6E4B5E;font-weight:600;font-size:{subtitle}px;",
            subtitle=16,
        )

        self.set_index(index)

    def set_index(self, index: int) -> None:
        self.title.setText(f"Raíz #{index}")

    def values(self) -> Tuple[str, str, str, str, str]:
        return (
            self.function_edit.text().strip(),
            self.a_edit.text().strip(),
            self.b_edit.text().strip(),
            self.tol_edit.text().strip(),
            self.approx_edit.text().strip(),
        )


class MetodoBiseccionWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Método de Bisección")
        self.root_cards: List[RootInputCard] = []

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(18)

        nav = QFrame()
        nav.setObjectName("TopNav")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(18, 12, 18, 12)
        nav_layout.setSpacing(12)

        self.btn_back = QPushButton("\u2190")
        self.btn_back.setObjectName("BackButton")
        self.btn_back.setFixedSize(42, 42)
        self.btn_back.setToolTip("Volver")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.clicked.connect(self._go_back)
        nav_layout.addWidget(self.btn_back)

        nav_layout.addSpacing(6)

        lbl_roots = QLabel("Cantidad de raíces:")
        nav_layout.addWidget(lbl_roots)

        self.root_count = QSpinBox()
        self.root_count.setRange(1, 10)
        self.root_count.setValue(1)
        self.root_count.valueChanged.connect(self._sync_root_cards)
        nav_layout.addWidget(self.root_count)

        nav_layout.addSpacing(12)

        self.btn_calcular = QPushButton("Calcular bisección")
        self.btn_calcular.setMinimumHeight(36)
        self.btn_calcular.clicked.connect(self._calcular)
        nav_layout.addWidget(self.btn_calcular)

        self.btn_limpiar = QPushButton("Limpiar formularios")
        self.btn_limpiar.setMinimumHeight(36)
        self.btn_limpiar.clicked.connect(self._limpiar)
        nav_layout.addWidget(self.btn_limpiar)

        nav_layout.addStretch(1)

        more_btn = QToolButton()
        more_btn.setAutoRaise(True)
        more_btn.setCursor(Qt.PointingHandCursor)
        more_btn.setToolTip("Más opciones")
        more_btn.setPopupMode(QToolButton.InstantPopup)
        try:
            from PySide6.QtCore import QSize
            bind_theme_icon(more_btn, make_overflow_icon, 20)
            more_btn.setIconSize(QSize(20, 20))
        except Exception:
            pass
        # sin tamaño fijo
        menu = QMenu(more_btn)
        act_settings = menu.addAction(gear_icon_preferred(22), "Configuración")
        act_settings.triggered.connect(self._open_settings)
        more_btn.setMenu(menu)
        nav_layout.addWidget(more_btn, 0, Qt.AlignVCenter)

        outer.addWidget(nav)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(18)

        title = QLabel("Método de Bisección")
        title.setObjectName("Title")
        card_layout.addWidget(title)

        subtitle = QLabel(
            "Ingresa la función, el intervalo [a, b] y la tolerancia para cada raíz. "
            "El método aplicará el criterio de paro |f(c)| < tolerancia exactamente como lo solicita el profesor."
        )
        subtitle.setObjectName("Subtitle")
        subtitle.setWordWrap(True)
        card_layout.addWidget(subtitle)

        subtitle_2 = QLabel(
            "Puedes calcular hasta diez raíces en una sola ejecución. Cada conjunto respetará el intervalo y "
            "validará que f(a) y f(b) tengan signos opuestos antes de iniciar."
        )
        subtitle_2.setObjectName("Subtitle")
        subtitle_2.setWordWrap(True)
        card_layout.addWidget(subtitle_2)

        forms_scroll = QScrollArea()
        forms_scroll.setWidgetResizable(True)
        self.forms_container = QWidget()
        self.forms_layout = QVBoxLayout(self.forms_container)
        self.forms_layout.setContentsMargins(0, 0, 0, 0)
        self.forms_layout.setSpacing(14)
        forms_scroll.setWidget(self.forms_container)
        card_layout.addWidget(forms_scroll, 1)

        outer.addWidget(card, 1)

        results_title = QLabel("Resultados")
        results_title.setObjectName("Title")
        outer.addWidget(results_title)

        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(16)
        self.results_scroll.setWidget(self.results_widget)
        outer.addWidget(self.results_scroll, 2)

        self._sync_root_cards()
        self._show_empty_results()

        install_toggle_shortcut(self)

    def _go_back(self):
        try:
            parent = self.parent()
            self.close()
            if parent is not None:
                parent.show()
                parent.activateWindow()
        except Exception:
            self.close()

    def _open_settings(self):
        open_settings_dialog(self)

    def _limpiar(self):
        for card in self.root_cards:
            card.function_edit.clear()
            card.a_edit.clear()
            card.b_edit.clear()
            card.tol_edit.clear()
            card.approx_edit.clear()
        self._show_empty_results()

    def _sync_root_cards(self):
        target = self.root_count.value()
        while len(self.root_cards) < target:
            card = RootInputCard(len(self.root_cards) + 1)
            self.root_cards.append(card)
            self.forms_layout.addWidget(card)
        while len(self.root_cards) > target:
            card = self.root_cards.pop()
            card.setParent(None)
        for idx, card in enumerate(self.root_cards, start=1):
            card.set_index(idx)

    def _calcular(self):
        resultados = []
        for idx, card in enumerate(self.root_cards, start=1):
            expr, a_txt, b_txt, tol_txt, approx_txt = card.values()
            try:
                func = _compile_function(expr)
                a = _parse_numeric(a_txt)
                b = _parse_numeric(b_txt)
                tol = _parse_numeric(tol_txt)
                if tol <= 0:
                    raise ValueError("La tolerancia debe ser positiva.")
                approx_value = None
                if approx_txt:
                    approx_value = _parse_numeric(approx_txt)
                pasos, raiz, fc, iteraciones = _run_bisection(func, a, b, tol)
            except Exception as exc:
                QMessageBox.warning(
                    self,
                    "Aviso",
                    f"No se pudo calcular la raíz #{idx}: {exc}",
                )
                return
            resultados.append((idx, expr, pasos, raiz, fc, iteraciones, approx_value))

        self._render_resultados(resultados)
        # Preguntar si el usuario desea ver la gráfica
        try:
            answer = QMessageBox.question(
                self,
                "Mostrar gráfica",
                "¿Desea ver la gráfica de la función y las raíces encontradas? (S/N):",
                QMessageBox.Yes | QMessageBox.No,
            )
        except Exception:
            answer = QMessageBox.No

        if answer == QMessageBox.Yes:
            try:
                self._plot_resultados(resultados)
            except Exception as exc:
                QMessageBox.warning(
                    self,
                    "Error al graficar",
                    f"Ocurrió un error al intentar graficar: {exc}",
                )

    def _create_table_widget(self, pasos: List[BisectionStep]) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(
            ["Iteración", "a", "b", "c", "f(a)", "f(b)", "f(c)"]
        )
        table.setRowCount(len(pasos))
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setObjectName("ResultsTable")
        table.setMinimumHeight(320)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        for row, paso in enumerate(pasos):
            values = [
                str(paso.iteration),
                _format_number(paso.a),
                _format_number(paso.b),
                _format_number(paso.c),
                _format_number(paso.fa),
                _format_number(paso.fb),
                _format_number(paso.fc),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, col, item)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        return table

    def _open_table_dialog(self, title: str, pasos: List[BisectionStep]) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(960, 600)
        dialog_layout = QVBoxLayout(dialog)
        dialog_table = self._create_table_widget(pasos)
        dialog_table.setMinimumHeight(0)
        dialog_layout.addWidget(dialog_table, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(dialog.reject)
        buttons.accepted.connect(dialog.accept)
        dialog_layout.addWidget(buttons)
        dialog.exec()

    def _render_resultados(self, resultados):
        for i in reversed(range(self.results_layout.count())):
            item = self.results_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        for idx, expr, pasos, raiz, fc, iteraciones, approx_value in resultados:
            card = QFrame()
            card.setObjectName("Card")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(28, 24, 28, 24)
            layout.setSpacing(18)

            title = QLabel(f"Raíz #{idx} - f(x) = {expr}")
            title.setObjectName("Subtitle")
            layout.addWidget(title)

            raiz_txt = _format_number(raiz)
            error_txt = _format_number(abs(fc))
            summary_lines = [
                f"El método converge con {iteraciones} iteraciones.",
                f"La raíz es: {raiz_txt}.",
                f"El margen de error es: {error_txt}.",
            ]
            if approx_value is not None:
                approx_txt = _format_number(approx_value)
                diff_txt = _format_number(abs(raiz - approx_value))
                summary_lines.append(
                    f"Comparación con tu valor aproximado {approx_txt}: diferencia = {diff_txt}."
                )
            summary = QLabel("\n".join(summary_lines))
            summary.setWordWrap(True)
            summary.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            bind_font_scale_stylesheet(
                summary,
                """
                QLabel {{
                    background-color: rgba(176, 122, 140, 0.18);
                    border-radius: 14px;
                    padding: 18px;
                    color: #6E4B5E;
                    font-size: {body}px;
                    font-weight: 600;
                    line-height: 150%;
                }}
                """,
                body=18,
            )
            layout.addWidget(summary)

            table = self._create_table_widget(pasos)
            layout.addWidget(table)

            btn_expand = QPushButton("Ver tabla en ventana amplia")
            btn_expand.setMinimumHeight(32)
            btn_expand.setCursor(Qt.PointingHandCursor)
            btn_expand.clicked.connect(
                lambda _checked=False, t=title.text(), ps=pasos: self._open_table_dialog(t, ps)
            )
            layout.addWidget(btn_expand, 0, Qt.AlignRight)

            self.results_layout.addWidget(card)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.results_layout.addWidget(spacer)

        self.results_scroll.verticalScrollBar().setValue(0)

    def _show_empty_results(self):
        for i in reversed(range(self.results_layout.count())):
            item = self.results_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        placeholder = QLabel(
            "Los resultados aparecerán aquí una vez que ejecutes el método."
        )
        placeholder.setAlignment(Qt.AlignCenter)
        bind_font_scale_stylesheet(
            placeholder,
            "color:#8F7A87;font-size:{body}px;font-style:italic;",
            body=16,
        )
        self.results_layout.addWidget(placeholder)

    def _plot_resultados(self, resultados):
        """
        Grafica las funciones y marca las raíces encontradas.

        `resultados` es una lista de tuplas:
            (idx, expr, pasos, raiz, fc, iteraciones, approx_value)

        Se re-compila cada función y se grafica en el rango de sus intervalos.
        Si hay varias raíces, la gráfica usa un rango que cubre todos los intervalos.
        """
        try:
            import matplotlib.pyplot as plt
        except Exception as exc:
            raise RuntimeError(
                "matplotlib no está disponible. Instala matplotlib para ver las gráficas."
            ) from exc

        try:
            import numpy as np
        except Exception:
            np = None

        # Recolectar rangos iniciales de cada resultado
        ranges = []
        for (_idx, _expr, pasos, _raiz, _fc, _it, _ap) in resultados:
            if not pasos:
                continue
            # pasos[0].a y pasos[0].b corresponden al intervalo inicial
            a0 = pasos[0].a
            b0 = pasos[0].b
            if a0 > b0:
                a0, b0 = b0, a0
            ranges.append((a0, b0))

        if not ranges:
            raise RuntimeError("No hay intervalos válidos para graficar.")

        global_min = min(r[0] for r in ranges)
        global_max = max(r[1] for r in ranges)

        # Si solo hay una raíz, centramos en ese intervalo
        if len(ranges) == 1:
            x_min, x_max = ranges[0]
        else:
            x_min, x_max = global_min, global_max

        # Añadir un pequeño padding
        span = x_max - x_min
        if span == 0:
            pad = abs(x_min) * 0.1 if x_min != 0 else 1.0
        else:
            pad = span * 0.12
        x_min -= pad
        x_max += pad

        # Preparar xs
        num_points = 800
        if np is not None:
            xs = np.linspace(x_min, x_max, num_points)
        else:
            xs = [x_min + (x_max - x_min) * i / (num_points - 1) for i in range(num_points)]

        fig, ax = plt.subplots(figsize=(10, 6))

        # Color/marker cycle
        colors = plt.rcParams.get("axes.prop_cycle").by_key().get("color", [])
        markers = ["o", "s", "^", "D", "v", "P", "X", "*", "+", "x"]

        for i, (idx, expr, pasos, raiz, fc, iteraciones, approx_value) in enumerate(resultados):
            try:
                func = _compile_function(expr)
            except Exception:
                # Saltar función que no compile
                continue

            # Evaluar y limpiar valores no válidos
            ys = []
            for x in xs:
                try:
                    y = func(float(x))
                except Exception:
                    y = float('nan')
                ys.append(y)

            color = colors[i % len(colors)] if colors else None
            # Graficar la curva de la función para este índice (con transparencia si hay muchas)
            ax.plot(xs, ys, label=f"f(x) #{idx}", color=color, linewidth=1.6, alpha=0.9)

            # Marcar intervalo original
            if pasos:
                a0 = pasos[0].a
                b0 = pasos[0].b
                ax.axvspan(min(a0, b0), max(a0, b0), alpha=0.08, color=color)

            # Marcar la raíz encontrada
            try:
                r_x = float(raiz)
                r_y = 0.0
                marker = markers[i % len(markers)]
                ax.plot(r_x, r_y, marker=marker, color=color, markersize=10, label=f"Raíz {i+1}")
            except Exception:
                pass

        # Eje X (y=0)
        ax.axhline(0.0, color="black", linewidth=0.9)

        ax.set_title("Gráfica de la función y raíces encontradas")
        ax.set_xlabel("Eje X")
        ax.set_ylabel("Eje Y")

        # Ajuste de límites y rejilla
        ax.set_xlim(x_min, x_max)
        ax.grid(True, linestyle='--', alpha=0.4)

        # Leyenda: queremos que las raíces aparezcan claras
        ax.legend()

        plt.tight_layout()
        plt.show()
