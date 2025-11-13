
from math import isfinite
import re
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
from ..text_utils import superscriptify

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


class ExponentInputFilter(QObject):
    """Convierte entrada de potencias a superíndices en un QLineEdit.

    Reglas:
    - Al teclear '^' inserta '⁽⁾' y coloca el cursor dentro; activa modo exponente.
    - Mientras esté activo el modo exponente, convierte 0-9, '+', '-', '(', ')', 'n'
      a sus equivalentes en superíndice.
    - Cualquier otra tecla sale del modo exponente y se procesa normalmente.
    """

    SUPERS = {
        "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
        "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
        "+": "⁺", "-": "⁻", "(": "⁽", ")": "⁾", "n": "ⁿ",
    }

    def __init__(self, edit: QLineEdit):
        super().__init__(edit)
        self.edit = edit
        self.in_exp_mode = False
        self._prev_star = False

    def eventFilter(self, obj, event):
        try:
            if obj is not self.edit:
                return False
            if event.type() != QEvent.KeyPress:
                return False
            text = event.text() or ""

            # Permitir saltar al superíndice con flecha derecha cuando hay plantilla ⁽⁾
            try:
                key = getattr(event, 'key', lambda: None)()
                if key == Qt.Key_Right:
                    s = self.edit.text() or ""
                    pos = self.edit.cursorPosition()
                    if pos < len(s) and s[pos:pos+2] == "⁽⁾":
                        # Colocar el cursor dentro del superíndice y activar modo exponente
                        self.edit.setCursorPosition(pos + 1)
                        self.in_exp_mode = True
                        return True
            except Exception:
                pass

            # Activar modo exponente con '^'
            if text == "^":
                self._insert("⁽⁾")
                # Colocar cursor entre paréntesis superíndice
                try:
                    pos = self.edit.cursorPosition()
                    self.edit.setCursorPosition(max(0, pos - 1))
                except Exception:
                    pass
                self.in_exp_mode = True
                self._prev_star = False
                return True

            # Detectar '**' y convertir a superíndice en vivo
            if text == "*":
                if self._prev_star:
                    try:
                        pos = self.edit.cursorPosition()
                        s = self.edit.text() or ""
                        if pos > 0 and s[pos-1] == '*':
                            new_s = s[:pos-1] + "⁽⁾" + s[pos:]
                            self.edit.setText(new_s)
                            # Cursor dentro del super-paréntesis
                            self.edit.setCursorPosition(pos)
                            self.in_exp_mode = True
                            self._prev_star = False
                            return True
                    except Exception:
                        pass
                # Primer '*': permitirlo y marcar
                self._prev_star = True
                return False

            if self.in_exp_mode:
                if text in self.SUPERS:
                    self._insert(self.SUPERS[text])
                    # Si el usuario cierra con ')', mantener modo por si sigue escribiendo
                    return True
                # Salir de modo exponente ante teclas no soportadas
                self.in_exp_mode = False
                self._prev_star = (text == '*')
                return False
            else:
                # Si no estamos en modo exponente, y no se tecleó '*', limpiar estado
                if text != '*':
                    self._prev_star = False
            return False
        except Exception:
            return False

    def _insert(self, s: str):
        try:
            pos = self.edit.cursorPosition()
            current = self.edit.text() or ""
            new_text = current[:pos] + s + current[pos:]
            self.edit.setText(new_text)
            self.edit.setCursorPosition(pos + len(s))
        except Exception:
            pass


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


def _normalize_expression(expr: str) -> str:
    expr = _pretty_to_ascii(expr)
    expr = expr.replace("==", "=")
    expr = expr.replace("^", "**")
    expr = expr.replace("{", "(").replace("}", ")")
    expr = expr.replace("[", "(").replace("]", ")")
    return _insert_implicit_multiplication(expr)


def _pretty_to_ascii(expr: str) -> str:
    """Convierte símbolos algebraicos visibles (√, superíndices) a una forma evaluable.

    - √x o √(x+1)  -> sqrt(x) / sqrt(x+1)
    - x², x⁻³, (x+1)⁴ -> x^(2), x^(-3), (x+1)^(4)
    """
    if not expr:
        return expr

    s = expr

    # 1) Raíz cuadrada: √( … )  -> sqrt( … )
    s = s.replace("√(", "sqrt(")

    # 1b) Raíz aplicada a un identificador/numero simple: √x, √2.5 -> sqrt(x), sqrt(2.5)
    s = re.sub(r"√\s*([A-Za-z]|\d(?:[\d\.]*))", r"sqrt(\1)", s)

    # 2) Potencias con superíndices: secuencia de superíndices tras un término
    supers_map = str.maketrans({
        "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
        "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
        "⁺": "+", "⁻": "-", "⁽": "(", "⁾": ")", "ⁿ": "n",
    })

    def _sup_repl(m: re.Match) -> str:
        base = m.group(1)
        sup = m.group(2)
        norm = sup.translate(supers_map)
        norm = norm.strip()
        if len(norm) <= 1 and norm not in ("(", ")"):
            return f"{base}^{norm}"
        return f"{base}^({norm})"

    # Aplica repetidamente por si hay múltiples ocurrencias
    pattern = re.compile(r"([A-Za-z0-9\)]+)([⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁽⁾ⁿ]+)")
    prev = None
    while prev != s:
        prev = s
        s = pattern.sub(_sup_repl, s)

    return s


def _insert_implicit_multiplication(expr: str) -> str:
    result_chars = []
    prev_non_space_idx = None

    for idx, ch in enumerate(expr):
        if prev_non_space_idx is not None and _needs_implicit_mul(expr, prev_non_space_idx, idx):
            result_chars.append("*")
        result_chars.append(ch)
        if not ch.isspace():
            prev_non_space_idx = idx
    return "".join(result_chars)


def _needs_implicit_mul(expr: str, prev_idx: int, curr_idx: int) -> bool:
    prev_char = expr[prev_idx]
    curr_char = expr[curr_idx]

    if curr_char.isspace():
        return False
    if prev_char in "+-*/%^=,":
        return False
    if curr_char in "+-*/%^=,)":
        return False
    if curr_char == ")":
        return False
    if prev_char == "(":
        return False

    prev_lower = prev_char.lower()
    curr_lower = curr_char.lower()

    if curr_lower == "x":
        return (
            prev_char.isdigit()
            or prev_char == "."
            or prev_char == ")"
            or prev_lower == "x"
        )

    if curr_char == "(":
        return (
            prev_char.isdigit()
            or prev_char == "."
            or prev_char == ")"
            or prev_lower == "x"
        )

    if curr_char.isdigit():
        return prev_lower == "x" or prev_char == ")"

    if curr_char.isalpha():
        if prev_char.isdigit() or prev_char == "." or prev_char == ")":
            if curr_lower in ("e",):
                return not _looks_like_scientific(expr, curr_idx)
            return True
        return False

    return False


def _looks_like_scientific(expr: str, e_idx: int) -> bool:
    next_idx = e_idx + 1
    length = len(expr)
    while next_idx < length and expr[next_idx].isspace():
        next_idx += 1
    if next_idx >= length:
        return False
    next_char = expr[next_idx]
    if next_char in "+-":
        next_idx += 1
        if next_idx >= length:
            return False
        next_char = expr[next_idx]
    if not next_char.isdigit():
        return False
    prev_idx = e_idx - 1
    while prev_idx >= 0 and expr[prev_idx].isspace():
        prev_idx -= 1
    if prev_idx < 0:
        return False
    prev_char = expr[prev_idx]
    if not (prev_char.isdigit() or prev_char == "."):
        return False
    return True

def _compile_function(expr: str) -> Callable[[float], float]:
    cleaned = (expr or "").strip()
    if not cleaned:
        raise ValueError("Ingrese una función f(x).")
    cleaned = _normalize_expression(cleaned)
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
        # La etiqueta se mantiene a la izquierda del campo de texto en la fila siguiente
        self.function_edit = QLineEdit()
        self.function_edit.setPlaceholderText("Ejemplo: x³ - x - 2")
        self.function_edit.setClearButtonEnabled(True)
        # Activar entrada de superíndices para potencias
        try:
            self._exp_filter = ExponentInputFilter(self.function_edit)
            self.function_edit.installEventFilter(self._exp_filter)
            # Si el botón de potencia del toolbar inserta '^', lo convertimos automáticamente
            self._in_text_update = False
            def _on_text_changed(_):
                if getattr(self, "_in_text_update", False):
                    return
                text = self.function_edit.text() or ""
                pos = self.function_edit.cursorPosition()

                SUPERS = {
                    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
                    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
                    "+": "⁺", "-": "⁻", "(": "⁽", ")": "⁾", "n": "ⁿ",
                }
                allowed = set("0123456789+-()n")

                i = 0
                new = []
                new_pos = pos
                changed = False
                length = len(text)
                while i < length:
                    ch = text[i]
                    # Tratar '**' como '^' para auto-superíndice
                    if ch == '*' and i + 1 < length and text[i+1] == '*':
                        ch = '^'
                        i += 1  # saltar el segundo '*'
                    if ch == '^':
                        j = i + 1
                        # recolectar contenido del exponente si existe
                        while j < length and text[j] in allowed:
                            j += 1
                        content = text[i+1:j]
                        # si no hay contenido aún, insertar paréntesis vacíos
                        if content:
                            sup = ''.join(SUPERS.get(c, c) for c in content)
                        else:
                            sup = ''
                        repl = '⁽' + sup + '⁾'
                        new.append(repl)
                        # ajustar caret
                        old_len = j - i
                        delta = len(repl) - old_len
                        if pos < i:
                            pass
                        elif pos <= j:
                            # cursor estaba dentro del exponente original
                            offset = pos - (i + 1)
                            new_pos = (len(''.join(new)) - len(repl)) + 1 + max(0, offset)
                            new_pos = min(new_pos, (len(''.join(new)) - 1))
                        else:
                            new_pos = pos + delta
                        i = j
                        changed = True
                        continue
                    new.append(ch)
                    i += 1

                if changed:
                    try:
                        self._in_text_update = True
                        new_text = ''.join(new)
                        self.function_edit.setText(new_text)
                        self.function_edit.setCursorPosition(max(0, min(len(new_text), new_pos)))
                        try:
                            # Asegurar que seguimos en modo exponente para convertir dígitos a superíndice
                            if hasattr(self, "_exp_filter"):
                                self._exp_filter.in_exp_mode = True
                        except Exception:
                            pass
                    finally:
                        self._in_text_update = False
            self.function_edit.textChanged.connect(_on_text_changed)
        except Exception:
            pass

        # Barra de atajos para funciones (para facilitar ingreso de f(x))
        self.func_toolbar = QWidget()
        ft_layout = QHBoxLayout(self.func_toolbar)
        ft_layout.setContentsMargins(0, 0, 0, 0)
        ft_layout.setSpacing(6)

        def add_btn(text: str, insert: str, cursor_offset: int = 0, tooltip=None):
            btn = QToolButton()
            btn.setText(text)
            btn.setAutoRaise(True)
            if tooltip:
                btn.setToolTip(tooltip)

            def _on_click(_checked=False, _insert=insert, _offset=cursor_offset):
                self._insert_into_line_edit(self.function_edit, _insert, _offset)

            btn.clicked.connect(_on_click)
            ft_layout.addWidget(btn)

        # Botones comúnes y funciones necesarias
        add_btn("x", "x", tooltip="Insertar variable x")
        add_btn("x²", "x**2", tooltip="Insertar x al cuadrado")
        # Plantilla de potencia: inserta x⁽⁾ y deja el cursor listo para escribir la base (después de x)
        add_btn("xⁿ", "x⁽⁾", cursor_offset=-2, tooltip="Potencia: x elevado a n (plantilla)")
        add_btn("()", "()", cursor_offset=-1, tooltip="Paréntesis")
        add_btn("√", "sqrt()", cursor_offset=-1, tooltip="Raíz: sqrt()")
        add_btn("sen", "sen()", cursor_offset=-1, tooltip="Seno")
        add_btn("cos", "cos()", cursor_offset=-1, tooltip="Coseno")
        add_btn("tan", "tan()", cursor_offset=-1, tooltip="Tangente")
        add_btn("ln", "ln()", cursor_offset=-1, tooltip="Logaritmo natural")
        add_btn("log", "log()", cursor_offset=-1, tooltip="Logaritmo base e (math.log)")
        add_btn("exp", "exp()", cursor_offset=-1, tooltip="Exponencial e^x")
        add_btn("e^x", "e**()", cursor_offset=-1, tooltip="Plantilla e^x")
        add_btn("abs", "abs()", cursor_offset=-1, tooltip="Valor absoluto")
        add_btn("π", "pi", tooltip="Constante pi")
        add_btn("e", "e", tooltip="Constante e")

        # Ubicar la barra de atajos arriba del campo de la función, ocupando columnas 1..3
        grid.addWidget(self.func_toolbar, 0, 1, 1, 3)

        # Ajuste visual: mostrar símbolos algebraicos en la barra de atajos
        try:
            while ft_layout.count():
                item = ft_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.deleteLater()

            add_btn("x", "x", tooltip="Insertar variable x")
            add_btn("x²", "x²", tooltip="Insertar x al cuadrado")
            # Misma plantilla visible con superíndice
            add_btn("xⁿ", "x⁽⁾", cursor_offset=-2, tooltip="Potencia: plantilla xⁿ")
            add_btn("()", "()", cursor_offset=-1, tooltip="Paréntesis")
            add_btn("√", "√()", cursor_offset=-1, tooltip="Raíz cuadrada: √( )")
            add_btn("sen", "sen()", cursor_offset=-1, tooltip="Seno")
            add_btn("cos", "cos()", cursor_offset=-1, tooltip="Coseno")
            add_btn("tan", "tan()", cursor_offset=-1, tooltip="Tangente")
            add_btn("ln", "ln()", cursor_offset=-1, tooltip="Logaritmo natural")
            add_btn("log", "log()", cursor_offset=-1, tooltip="Logaritmo base e (math.log)")
            add_btn("exp", "exp()", cursor_offset=-1, tooltip="Exponencial e^x")
            add_btn("e^x", "e**()", cursor_offset=-1, tooltip="Plantilla e^x")
            add_btn("abs", "abs()", cursor_offset=-1, tooltip="Valor absoluto")
            add_btn("π", "pi", tooltip="Constante pi")
            add_btn("e", "e", tooltip="Constante e")
        except Exception:
            pass

        # Ahora ubicar etiqueta y campo de función en la fila 1, con el campo más largo (columnas 1..3)
        grid.addWidget(self.lbl_func, 1, 0)
        grid.addWidget(self.function_edit, 1, 1, 1, 3)

        self.lbl_intervalo = QLabel("Intervalo [a, b]:")
        self.lbl_intervalo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.lbl_intervalo, 2, 0)

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
        grid.addWidget(self.interval_widget, 2, 1, 1, 3)

        self.lbl_tol = QLabel("Tolerancia:")
        self.lbl_tol.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.lbl_tol, 3, 0)
        self.tol_edit = QLineEdit()
        self.tol_edit.setPlaceholderText("Ejemplo: 0.0001")
        self.tol_edit.setAlignment(Qt.AlignCenter)
        self.tol_edit.setClearButtonEnabled(True)
        grid.addWidget(self.tol_edit, 3, 1, 1, 3)

        self.lbl_aprox = QLabel("Valor aproximado (opcional):")
        self.lbl_aprox.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.lbl_aprox, 4, 0)
        self.approx_edit = QLineEdit()
        self.approx_edit.setPlaceholderText("Ejemplo: 1.2")
        self.approx_edit.setAlignment(Qt.AlignCenter)
        self.approx_edit.setClearButtonEnabled(True)
        self.approx_edit.setToolTip("Ingresa un valor esperado para comparar, deja vacío si no aplica.")
        grid.addWidget(self.approx_edit, 4, 1, 1, 3)
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
            self.func_toolbar,
            self.lbl_tol,
            self.tol_edit,
            self.lbl_aprox,
            self.approx_edit,
        ):
            w.setVisible(is_primary)

    def _insert_into_line_edit(self, edit: QLineEdit, text: str, cursor_offset: int = 0) -> None:
        try:
            pos = edit.cursorPosition()
            current = edit.text() or ""
            new_text = current[:pos] + text + current[pos:]
            edit.setText(new_text)
            new_pos = max(0, min(len(new_text), pos + len(text) + cursor_offset))
            edit.setCursorPosition(new_pos)
            edit.setFocus()
        except Exception:
            # En caso de cualquier error, degradar a un append simple
            edit.setText((edit.text() or "") + text)
            try:
                edit.setCursorPosition(len(edit.text()))
            except Exception:
                pass

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
        skip_additional = False
        skip_additional = False

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
            # Rellenar los text boxes de los intervalos detectados en las tarjetas
            try:
                total = len(intervals)
                if total > 0:
                    if self.root_count.value() < total:
                        self.root_count.setValue(total)
                    for idx_i, (a_det, b_det) in enumerate(intervals, start=1):
                        if idx_i - 1 < len(self.root_cards):
                            card_i = self.root_cards[idx_i - 1]
                            try:
                                card_i.a_edit.setText(_format_number(a_det))
                                card_i.b_edit.setText(_format_number(b_det))
                            except Exception:
                                pass
            except Exception:
                pass
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
                QMessageBox.warning(self, "Aviso", "No se encontraron ra??ces en los intervalos detectados.")
                return
            skip_additional = True

        # Procesar ra??ces adicionales: solo requieren intervalos, reutilizan expr1 y tol
        if not skip_additional:
            for card_idx, card in enumerate(self.root_cards[1:], start=2):
                _expr, a_txt, b_txt, _tol_txt, _approx_txt = card.values()
                if not (a_txt and b_txt):
                    # Si no hay intervalo, omitir esta tarjeta pero no abortar el resto
                    QMessageBox.warning(self, "Aviso", f"La ra??z #{card_idx} no tiene intervalo. Se omitiro.")
                    continue
                try:
                    a = _parse_numeric(a_txt)
                    b = _parse_numeric(b_txt)
                except Exception as exc:
                    QMessageBox.warning(self, "Aviso", f"Intervalo involido en la ra??z #{card_idx}: {exc}")
                    continue
                try:
                    pasos, raiz, fc, iteraciones = _run_bisection(func, a, b, tol)
                    resultados.append((display_idx, expr1, pasos, raiz, fc, iteraciones, None))
                    display_idx += 1
                except Exception as exc:
                    QMessageBox.warning(self, "Aviso", f"No se pudo calcular la ra??z #{card_idx} (intervalo [{a}, {b}]): {exc}")
                    continue
        # Quitar duplicados por valor de ra�z
        _unique_res = []
        _seen_keys = set()
        for _it in resultados:
            try:
                _key = round(float(_it[3]), 10)
            except Exception:
                _key = _it[3]
            if _key in _seen_keys:
                continue
            _seen_keys.add(_key)
            _unique_res.append(_it)
        resultados = _unique_res
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

            # Mostrar la función con potencias en superíndice para mejor lectura
            title = QLabel(f"Raíz #{idx} - f(x) = {superscriptify(expr)}")
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
            # Agregar intervalo utilizado si está disponible en los pasos
            try:
                if pasos:
                    a0 = _format_number(pasos[0].a)
                    b0 = _format_number(pasos[0].b)
                    summary_lines.insert(1, f"Intervalo usado: [{a0}, {b0}].")
            except Exception:
                pass
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

