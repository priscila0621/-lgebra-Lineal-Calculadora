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
    QStyle,
    QListWidget,
)
from PySide6.QtCore import Qt, QObject, QEvent
from PySide6.QtGui import QFontMetrics

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
        # Alias comunes
        "ln": math.log,
        # Trigonométricas en español y variantes
        "sen": math.sin,
        "tg": math.tan,
        "ctg": (lambda x: 1.0 / math.tan(x)),
        "cosec": (lambda x: 1.0 / math.sin(x)),
        "csc": (lambda x: 1.0 / math.sin(x)),
        "sec": (lambda x: 1.0 / math.cos(x)),
        # Inversas/arcotrigonométricas
        "arcsen": math.asin,
        "asen": math.asin,
        "arctg": math.atan,
        "atg": math.atan,
        # Otros alias útiles
        "raiz": math.sqrt,
    }
)


class TableZoomFilter(QObject):
    """Permite hacer zoom en tablas con Ctrl + rueda del ratón."""
    def eventFilter(self, obj, event):
        try:
            if event.type() == QEvent.Wheel and hasattr(event, 'angleDelta'):
                # En Qt6, QWheelEvent tiene modifiers()
                modifiers = getattr(event, 'modifiers', lambda: Qt.NoModifier)()
                if modifiers & Qt.ControlModifier:
                    delta = event.angleDelta().y()
                    font = obj.font()
                    size = font.pointSize() or 10
                    size += 1 if delta > 0 else -1
                    size = max(8, min(28, size))
                    font.setPointSize(size)
                    obj.setFont(font)
                    try:
                        # Ajuste de altura de filas según la fuente
                        fm = QFontMetrics(font)
                        h = int(fm.height() * 1.6)
                        obj.verticalHeader().setDefaultSectionSize(h)
                        obj.horizontalHeader().setFont(font)
                    except Exception:
                        pass
                    obj.viewport().update()
                    return True
        except Exception:
            pass
        return False


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
    cleaned = cleaned.replace("{", "(").replace("}", ")")
    cleaned = cleaned.replace("{", "(").replace("}", ")")
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
    cleaned = cleaned.replace("^", "**").replace("{", "(").replace("}", ")")
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


def _detect_sign_change_intervals(
    func: Callable[[float], float],
    start: float = -10.0,
    end: float = 10.0,
    step: float = 0.5,
) -> List[Tuple[float, float]]:
    """
    Scanea el rango [start, end] con paso `step` y devuelve una lista de
    intervalos (a, b) donde la función cambia de signo (f(a)*f(b) < 0).

    Valores que provocan excepciones o no finitos se ignoran.
    """
    intervals: List[Tuple[float, float]] = []
    if step <= 0:
        raise ValueError("El paso debe ser positivo.")
    # Asegurar start <= end
    if start > end:
        start, end = end, start
    # Número de pasos aproximado
    n_steps = max(1, int(math.ceil((end - start) / step)))
    xs = [start + i * step for i in range(n_steps + 1)]
    # Asegurar que el último valor sea exactamente end
    if xs[-1] < end:
        xs.append(end)

    prev_x = None
    prev_y = None
    for x in xs:
        try:
            y = func(float(x))
            if not isfinite(y):
                # ignorar
                prev_x, prev_y = x, None
                continue
        except Exception:
            prev_x, prev_y = x, None
            continue

        if prev_x is not None and prev_y is not None:
            try:
                if prev_y * y < 0:
                    intervals.append((prev_x, x))
            except Exception:
                pass

        prev_x, prev_y = x, y

    return intervals


class IntervalsDialog(QDialog):
    """Dialogo que muestra los intervalos detectados y permite ajustar
    start/end/step antes de confirmar."""

    def __init__(self, parent, func: Callable[[float], float], start: float = -10.0, end: float = 10.0, step: float = 0.5):
        super().__init__(parent)
        self.setWindowTitle("Intervalos detectados")
        self.resize(560, 420)
        self.func = func

        layout = QVBoxLayout(self)

        info = QLabel("Se encontraron los siguientes intervalos donde f(x) cambia de signo. "
                      "Puedes ajustar los parámetros de búsqueda y volver a detectar.")
        info.setWordWrap(True)
        layout.addWidget(info)

        params_row = QHBoxLayout()
        params_row.addWidget(QLabel("Inicio:"))
        self.start_edit = QLineEdit(str(start))
        self.start_edit.setFixedWidth(100)
        params_row.addWidget(self.start_edit)
        params_row.addWidget(QLabel("Fin:"))
        self.end_edit = QLineEdit(str(end))
        self.end_edit.setFixedWidth(100)
        params_row.addWidget(self.end_edit)
        params_row.addWidget(QLabel("Paso:"))
        self.step_edit = QLineEdit(str(step))
        self.step_edit.setFixedWidth(100)
        params_row.addWidget(self.step_edit)
        params_row.addStretch(1)
        layout.addLayout(params_row)

        btn_row = QHBoxLayout()
        self.refresh_btn = QPushButton("Detectar")
        self.refresh_btn.clicked.connect(self._on_refresh)
        btn_row.addWidget(self.refresh_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # inicializar lista
        self._run_detection()

    def _run_detection(self):
        try:
            s = _parse_numeric(self.start_edit.text())
            e = _parse_numeric(self.end_edit.text())
            st = _parse_numeric(self.step_edit.text())
        except Exception as exc:
            QMessageBox.warning(self, "Parámetros inválidos", f"Parámetros de búsqueda inválidos: {exc}")
            return
        try:
            intervals = _detect_sign_change_intervals(self.func, s, e, st)
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"No se pudo detectar intervalos: {exc}")
            intervals = []

        self.list_widget.clear()
        for a, b in intervals:
            self.list_widget.addItem(f"[{_format_number(a)}, {_format_number(b)}]")

        if not intervals:
            self.list_widget.addItem("(No se detectaron intervalos en los parámetros provistos.)")

    def _on_refresh(self):
        self._run_detection()

    def get_intervals(self) -> List[Tuple[float, float]]:
        try:
            s = _parse_numeric(self.start_edit.text())
            e = _parse_numeric(self.end_edit.text())
            st = _parse_numeric(self.step_edit.text())
        except Exception:
            return []
        try:
            return _detect_sign_change_intervals(self.func, s, e, st)
        except Exception:
            return []


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

        self.lbl_func = QLabel("f(x):")
        self.lbl_func.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.lbl_func, 0, 0)
        self.function_edit = QLineEdit()
        self.function_edit.setPlaceholderText("Ejemplo: x**3 - x - 2")
        self.function_edit.setClearButtonEnabled(True)
        grid.addWidget(self.function_edit, 0, 1, 1, 2)

        self.lbl_intervalo = QLabel("Intervalo [a, b]:")
        self.lbl_intervalo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.lbl_intervalo, 1, 0)

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

        self.interval_widget = interval_widget
        grid.addWidget(self.interval_widget, 1, 1, 1, 3)

        self.lbl_tol = QLabel("Tolerancia:")
        self.lbl_tol.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.lbl_tol, 2, 0)
        self.tol_edit = QLineEdit()
        self.tol_edit.setPlaceholderText("Ejemplo: 0.0001")
        self.tol_edit.setAlignment(Qt.AlignCenter)
        self.tol_edit.setClearButtonEnabled(True)
        grid.addWidget(self.tol_edit, 2, 1, 1, 3)

        self.lbl_aprox = QLabel("Valor aproximado (opcional):")
        self.lbl_aprox.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.lbl_aprox, 3, 0)
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

    def set_primary_mode(self, is_primary: bool) -> None:
        # En modo primario: mostrar todos los campos.
        # En modo secundario: solo pedir intervalos; ocultar f(x), tolerancia y aproximado.
        for w in (
            self.lbl_func,
            self.function_edit,
            self.lbl_tol,
            self.tol_edit,
            self.lbl_aprox,
            self.approx_edit,
        ):
            w.setVisible(is_primary)

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

        # Un solo scroll para toda la ventana
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        central = QWidget()
        main_scroll.setWidget(central)
        self.setCentralWidget(main_scroll)
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
        # Botón de calcular se reubica al final del formulario (ver más abajo)

        self.btn_limpiar = QPushButton("Limpiar formularios")
        self.btn_limpiar.setMinimumHeight(36)
        self.btn_limpiar.clicked.connect(self._limpiar)
        # Botón de limpiar se reubica al final del formulario

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
            "Para la primera raíz ingresa f(x), el intervalo [a, b], la tolerancia y (opcional) un aproximado. "
            "Para las siguientes raíces solo ingresa el intervalo [a, b]."
        )
        subtitle.setObjectName("Subtitle")
        subtitle.setWordWrap(True)
        card_layout.addWidget(subtitle)

        subtitle_2 = QLabel(
            "Puedes calcular hasta diez raíces reutilizando la misma f(x) y tolerancia de la primera. "
            "Cada intervalo validará que f(a) y f(b) tengan signos opuestos antes de iniciar."
        )
        subtitle_2.setObjectName("Subtitle")
        subtitle_2.setWordWrap(True)
        card_layout.addWidget(subtitle_2)

        self.forms_container = QWidget()
        self.forms_layout = QVBoxLayout(self.forms_container)
        self.forms_layout.setContentsMargins(0, 0, 0, 0)
        self.forms_layout.setSpacing(14)
        card_layout.addWidget(self.forms_container, 1)
        # Acciones al final del formulario
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)
        actions_row.addStretch(1)
        actions_row.addWidget(self.btn_limpiar)
        actions_row.addWidget(self.btn_calcular)
        card_layout.addLayout(actions_row)

        # Tarjeta para la gráfica interactiva (derecha)
        self.plot_card = QFrame()
        self.plot_card.setObjectName("Card")
        _plot_outer = QVBoxLayout(self.plot_card)
        _plot_outer.setContentsMargins(24, 20, 24, 20)
        _plot_outer.setSpacing(10)
        _plot_title = QLabel("Gráfica interactiva")
        _plot_title.setObjectName("Title")
        _plot_outer.addWidget(_plot_title)
        self.plot_container = QWidget()
        self.plot_container_layout = QVBoxLayout(self.plot_container)
        self.plot_container_layout.setContentsMargins(0, 0, 0, 0)
        self.plot_container_layout.setSpacing(6)
        _plot_outer.addWidget(self.plot_container, 1)
        try:
            self._init_plot_area()
        except Exception:
            pass

        # Disposición superior en dos columnas (izquierda: formularios, derecha: gráfica)
        top_row = QWidget()
        top_layout = QHBoxLayout(top_row)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(16)
        top_layout.addWidget(card, 2)
        top_layout.addWidget(self.plot_card, 3)
        outer.addWidget(top_row, 2)

        results_title = QLabel("Resultados")
        results_title.setObjectName("Title")
        outer.addWidget(results_title)

        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(16)
        outer.addWidget(self.results_widget, 2)

        self._sync_root_cards()
        self._show_empty_results()
        try:
            self._update_plot_live()
        except Exception:
            pass

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
        try:
            self._update_plot_live()
        except Exception:
            pass

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
            # Solo la primera raíz muestra f(x), tolerancia y aproximado
            card.set_primary_mode(idx == 1)
        # Conectar señales para actualizar la gráfica interactiva
        for card in self.root_cards:
            try:
                card.function_edit.textChanged.disconnect()
            except Exception:
                pass
            try:
                card.a_edit.textChanged.disconnect()
            except Exception:
                pass
            try:
                card.b_edit.textChanged.disconnect()
            except Exception:
                pass
            try:
                card.function_edit.textChanged.connect(self._update_plot_live)
                card.a_edit.textChanged.connect(self._update_plot_live)
                card.b_edit.textChanged.connect(self._update_plot_live)
            except Exception:
                pass
        try:
            self._update_plot_live()
        except Exception:
            pass

    def _calcular(self):
        resultados = []
        display_idx = 1

        if not self.root_cards:
            QMessageBox.warning(self, "Aviso", "No hay formularios disponibles.")
            return

        # Tomar función y tolerancia de la primera raíz
        first_card = self.root_cards[0]
        expr1, a1_txt, b1_txt, tol1_txt, approx1_txt = first_card.values()
        expr1 = (expr1 or "").strip()
        if not expr1:
            QMessageBox.warning(self, "Aviso", "Ingresa la función f(x) en la primera raíz.")
            return
        try:
            func = _compile_function(expr1)
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"La función en la primera raíz no es válida: {exc}")
            return

        try:
            tol = _parse_numeric(tol1_txt)
            if tol <= 0:
                raise ValueError("La tolerancia debe ser positiva.")
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"Tolerancia inválida (primera raíz): {exc}")
            return

        approx1_value = None
        if approx1_txt:
            try:
                approx1_value = _parse_numeric(approx1_txt)
            except Exception:
                approx1_value = None

        # Procesar primera raíz (permite detección automática si no hay [a,b])
        if a1_txt and b1_txt:
            try:
                a1 = _parse_numeric(a1_txt)
                b1 = _parse_numeric(b1_txt)
            except Exception as exc:
                QMessageBox.warning(self, "Aviso", f"Intervalo inválido (primera raíz): {exc}")
                return
            try:
                pasos, raiz, fc, iteraciones = _run_bisection(func, a1, b1, tol)
                resultados.append((display_idx, expr1, pasos, raiz, fc, iteraciones, approx1_value))
                display_idx += 1
            except Exception as exc:
                QMessageBox.warning(self, "Aviso", f"No se pudo calcular la raíz (intervalo [{a1}, {b1}]): {exc}")
        else:
            # Detección automática para la primera raíz si no hay intervalo
            dlg = IntervalsDialog(self, func, start=-10.0, end=10.0, step=0.5)
            if dlg.exec() != QDialog.Accepted:
                return
            intervals = dlg.get_intervals()
            if not intervals:
                QMessageBox.warning(self, "Aviso", "No se detectaron intervalos donde la función cambie de signo.")
                return
            any_success = False
            for a, b in intervals:
                try:
                    pasos, raiz, fc, iteraciones = _run_bisection(func, a, b, tol)
                    resultados.append((display_idx, expr1, pasos, raiz, fc, iteraciones, approx1_value))
                    display_idx += 1
                    any_success = True
                except Exception as exc:
                    QMessageBox.warning(self, "Aviso", f"Bisección en [{a}, {b}] falló: {exc}")
                    continue
            if not any_success:
                QMessageBox.warning(self, "Aviso", "No se encontraron raíces en los intervalos detectados.")
                return

        # Procesar raíces adicionales: solo requieren intervalos, reutilizan expr1 y tol
        for card_idx, card in enumerate(self.root_cards[1:], start=2):
            _expr, a_txt, b_txt, _tol_txt, _approx_txt = card.values()
            if not (a_txt and b_txt):
                # Si no hay intervalo, omitir esta tarjeta pero no abortar el resto
                QMessageBox.warning(self, "Aviso", f"La raíz #{card_idx} no tiene intervalo. Se omitirá.")
                continue
            try:
                a = _parse_numeric(a_txt)
                b = _parse_numeric(b_txt)
            except Exception as exc:
                QMessageBox.warning(self, "Aviso", f"Intervalo inválido en la raíz #{card_idx}: {exc}")
                continue
            try:
                pasos, raiz, fc, iteraciones = _run_bisection(func, a, b, tol)
                resultados.append((display_idx, expr1, pasos, raiz, fc, iteraciones, None))
                display_idx += 1
            except Exception as exc:
                QMessageBox.warning(self, "Aviso", f"No se pudo calcular la raíz #{card_idx} (intervalo [{a}, {b}]): {exc}")
                continue

        if not resultados:
            QMessageBox.information(self, "Resultados", "No se encontraron raíces para los intervalos ingresados.")
            return

        self._render_resultados(resultados)
        self._draw_results_on_canvas(resultados)

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
            # Reemplazo: fila de título con icono pequeño para expandir la tabla
            title_row = QHBoxLayout()
            title_row.setContentsMargins(0, 0, 0, 0)
            title_row.setSpacing(8)
            title_row.addWidget(title)
            title_row.addStretch(1)
            expand_btn = QToolButton()
            expand_btn.setAutoRaise(True)
            expand_btn.setCursor(Qt.PointingHandCursor)
            expand_btn.setToolTip("Abrir tabla en ventana amplia")
            try:
                icon = self.style().standardIcon(QStyle.SP_TitleBarMaxButton)
                expand_btn.setIcon(icon)
            except Exception:
                expand_btn.setText("↗")
            expand_btn.clicked.connect(
                lambda _checked=False, t=lambda: title.text(), ps=pasos: self._open_table_dialog(t(), ps)
            )
            # quitar el título agregado y reemplazar por la fila con icono
            try:
                item = layout.takeAt(layout.count() - 1)
                if item is not None:
                    w = item.widget()
                    if w is not None:
                        w.setParent(None)
            except Exception:
                pass
            layout.addLayout(title_row)

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

            # Botón reemplazado por icono en la fila del título

            self.results_layout.addWidget(card)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.results_layout.addWidget(spacer)


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

    # --- Integración de gráfica interactiva embebida ---
    def _init_plot_area(self):
        try:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
            import matplotlib.pyplot as plt
        except Exception:
            placeholder = QLabel("Instala matplotlib para ver la gráfica interactiva.")
            placeholder.setAlignment(Qt.AlignCenter)
            self.plot_container_layout.addWidget(placeholder)
            self._mpl_ready = False
            return

        self._mpl_ready = True
        self._mpl = {}
        self._mpl['plt'] = plt
        self._mpl['fig'], self._mpl['ax'] = plt.subplots(figsize=(8, 4))
        self._mpl['canvas'] = FigureCanvas(self._mpl['fig'])
        self._mpl['toolbar'] = NavigationToolbar(self._mpl['canvas'], self)
        self._mpl['ax'].grid(True, linestyle='--', alpha=0.3)
        self._mpl['ax'].set_title("f(x)")
        self._mpl['ax'].set_xlabel("Eje X")
        self._mpl['ax'].set_ylabel("Eje Y")
        self.plot_container_layout.addWidget(self._mpl['toolbar'])
        self.plot_container_layout.addWidget(self._mpl['canvas'], 1)
        try:
            # Zoom con rueda del ratón sobre la gráfica
            self._mpl['cid_scroll'] = self._mpl['canvas'].mpl_connect('scroll_event', self._on_canvas_scroll)
        except Exception:
            pass

    def _current_x_range(self):
        xs = []
        for card in self.root_cards:
            try:
                a = _parse_numeric(card.a_edit.text().strip())
                b = _parse_numeric(card.b_edit.text().strip())
                xs.append(min(a, b))
                xs.append(max(a, b))
            except Exception:
                continue
        if xs:
            x_min, x_max = min(xs), max(xs)
            if x_min == x_max:
                pad = abs(x_min) * 0.5 if x_min != 0 else 5.0
                return x_min - pad, x_max + pad
            pad = (x_max - x_min) * 0.15
            return x_min - pad, x_max + pad
        return -10.0, 10.0

    def _update_plot_live(self):
        if not getattr(self, '_mpl_ready', False):
            return
        plt = self._mpl['plt']
        ax = self._mpl['ax']
        ax.clear()
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.set_xlabel("Eje X")
        ax.set_ylabel("Eje Y")
        ax.axhline(0.0, color='black', linewidth=0.9)
        x_min, x_max = self._current_x_range()
        try:
            import numpy as np
        except Exception:
            np = None
        num_points = 600
        if np is not None:
            xs = np.linspace(x_min, x_max, num_points)
        else:
            xs = [x_min + (x_max - x_min) * i / (num_points - 1) for i in range(num_points)]

        plotted = False
        for idx, card in enumerate(self.root_cards, start=1):
            expr = (card.function_edit.text() or "").strip()
            if not expr:
                continue
            try:
                func = _compile_function(expr)
            except Exception:
                continue
            ys = []
            for x in xs:
                try:
                    y = func(float(x))
                except Exception:
                    y = float('nan')
                ys.append(y)
            ax.plot(xs, ys, label=f"f(x) #{idx}", linewidth=1.6, alpha=0.9)
            try:
                a = _parse_numeric(card.a_edit.text().strip())
                b = _parse_numeric(card.b_edit.text().strip())
                ax.axvspan(min(a, b), max(a, b), alpha=0.08)
            except Exception:
                pass
            plotted = True

        if plotted:
            ax.set_xlim(x_min, x_max)
            ax.legend()
            ax.set_title("Vista previa: ajusta la función e intervalos")
        else:
            ax.set_title("Escribe f(x) para previsualizar la curva")
        self._mpl['canvas'].draw_idle()

    def _draw_results_on_canvas(self, resultados):
        if not getattr(self, '_mpl_ready', False):
            return
        plt = self._mpl['plt']
        ax = self._mpl['ax']
        ax.clear()
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.set_xlabel("Eje X")
        ax.set_ylabel("Eje Y")
        ax.axhline(0.0, color='black', linewidth=0.9)
        ranges = []
        for (_idx, _expr, pasos, _raiz, _fc, _it, _ap) in resultados:
            if pasos:
                a0 = pasos[0].a
                b0 = pasos[0].b
                ranges.append((min(a0, b0), max(a0, b0)))
        if ranges:
            x_min = min(r[0] for r in ranges)
            x_max = max(r[1] for r in ranges)
            span = x_max - x_min
            pad = span * 0.15 if span else 1.0
            x_min -= pad
            x_max += pad
        else:
            x_min, x_max = self._current_x_range()
        try:
            import numpy as np
        except Exception:
            np = None
        num_points = 800
        if np is not None:
            xs = np.linspace(x_min, x_max, num_points)
        else:
            xs = [x_min + (x_max - x_min) * i / (num_points - 1) for i in range(num_points)]
        colors = plt.rcParams.get("axes.prop_cycle").by_key().get("color", [])
        markers = ["o", "s", "^", "D", "v", "P", "X", "*", "+", "x"]
        for i, (idx, expr, pasos, raiz, fc, iteraciones, approx_value) in enumerate(resultados):
            try:
                func = _compile_function(expr)
            except Exception:
                continue
            ys = []
            for x in xs:
                try:
                    y = func(float(x))
                except Exception:
                    y = float('nan')
                ys.append(y)
            color = colors[i % len(colors)] if colors else None
            ax.plot(xs, ys, label=f"f(x) #{idx}", color=color, linewidth=1.6, alpha=0.9)
            if pasos:
                a0 = pasos[0].a
                b0 = pasos[0].b
                ax.axvspan(min(a0, b0), max(a0, b0), alpha=0.08, color=color)
            try:
                rx = float(raiz)
                marker = markers[i % len(markers)]
                ax.plot(rx, 0.0, marker=marker, color=color, markersize=10, label=f"Raíz {i+1}")
            except Exception:
                pass
        ax.set_xlim(x_min, x_max)
        ax.legend()
        ax.set_title("Resultados de bisección")
        self._mpl['canvas'].draw_idle()

    def _on_canvas_scroll(self, event):
        # Zoom con rueda del ratón en matplotlib (centra en el cursor)
        try:
            if not getattr(self, '_mpl_ready', False):
                return
            ax = self._mpl['ax']
            # Ignorar si no hay datos de eje (p. ej. fuera del gráfico)
            if event.xdata is None or event.ydata is None:
                return
            # Determinar factor de zoom
            base = 1.2
            scale = 1.0 / base if getattr(event, 'button', 'up') == 'up' else base
            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()
            xdata = float(event.xdata)
            ydata = float(event.ydata)
            # Reescalar manteniendo el punto del cursor como ancla
            left = xdata - (xdata - cur_xlim[0]) * scale
            right = xdata + (cur_xlim[1] - xdata) * scale
            bottom = ydata - (ydata - cur_ylim[0]) * scale
            top = ydata + (cur_ylim[1] - ydata) * scale
            # Evitar colapsar a rangos inválidos
            if right - left < 1e-9 or top - bottom < 1e-9:
                return
            ax.set_xlim(left, right)
            ax.set_ylim(bottom, top)
            self._mpl['canvas'].draw_idle()
        except Exception:
            pass

